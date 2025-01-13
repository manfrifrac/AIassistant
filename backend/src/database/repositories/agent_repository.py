from typing import Optional, List, Dict, Any, Union
from sqlalchemy import select, update, and_
from datetime import datetime
import json
from backend.src.models.agent import Agent
from .base_repository import BaseRepository
from ..exceptions import QueryError

class AgentRepository(BaseRepository[Agent]):
    def __init__(self):
        super().__init__("agents", Agent)

    def _validate_parameters(self, parameters: Union[str, dict]) -> dict:
        """Validate and convert parameters to dict"""
        if isinstance(parameters, str):
            try:
                params_dict = json.loads(parameters)
            except json.JSONDecodeError as e:
                raise QueryError(f"Invalid parameters JSON: {str(e)}")
        else:
            params_dict = parameters

        if not isinstance(params_dict, dict):
            raise QueryError("Parameters must be a dictionary")
        return params_dict

    def _create_agent_model(self, *, name: str, task: str, parameters: Union[str, dict]) -> Agent:
        """Create an agent model with validation"""
        now = datetime.now()
        params_dict = self._validate_parameters(parameters)

        return Agent(
            name=name,
            task=task,
            parameters=params_dict,
            created_at=now,
            updated_at=now
        )

    async def create_agent(self, name: str, task: str, parameters: Union[str, dict]) -> Agent:
        """Create a new agent with the given configuration"""
        try:
            model = self._create_agent_model(name=name, task=task, parameters=parameters)
            return await super().create(model)
        except Exception as e:
            raise QueryError(f"Failed to create agent: {str(e)}")

    async def update_agent_status(self, agent_id: str, available: bool) -> Agent:
        """Update agent availability status"""
        try:
            async with self.db.get_session() as session:
                stmt = (
                    update(self.table)
                    .where(self.table.c.id == agent_id)
                    .values(is_available=available, updated_at=datetime.now())
                    .returning(*self.table.c)
                )
                result = await session.execute(stmt)
                row = result.fetchone()
                if not row:
                    raise QueryError(f"Agent {agent_id} not found")
                await session.commit()
                agent = self._row_to_model(row)
                if agent is None:
                    return Agent(
                        name="default",
                        task="default",
                        parameters={},
                        created_at=datetime.now(),
                        updated_at=datetime.now()
                    )
                return agent
        except Exception as e:
            raise QueryError(f"Failed to update agent status: {str(e)}")

    async def get_all(self) -> List[Agent]:
        query = select(self.table)
        async with self.db.get_session() as session:
            result = await session.execute(query)
            rows = result.fetchall()
            return [agent for row in rows 
                   if (agent := self._row_to_model(row)) is not None]
