import os
import pytest
import tempfile
import yaml
from typing import Type

from pydantic import BaseModel, Field

from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task, tool
from crewai.tools import BaseTool

def test_function_calling_llm_in_yaml():
    """
    Test function_calling_llm YAML configuration.
    
    Tests:
        - Direct model name specification
        - Configuration persistence
        - Integration with Agent initialization
    """
    # Create temporary YAML files
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create agents.yaml with function_calling_llm
        agents_yaml = os.path.join(temp_dir, "agents.yaml")
        with open(agents_yaml, "w") as f:
            yaml.dump(
                {
                    "test_agent": {
                        "role": "Test Agent",
                        "goal": "Test Goal",
                        "backstory": "Test Backstory",
                        "function_calling_llm": "gpt-4o-mini"
                    }
                },
                f
            )
        
        # Create tasks.yaml
        tasks_yaml = os.path.join(temp_dir, "tasks.yaml")
        with open(tasks_yaml, "w") as f:
            yaml.dump(
                {
                    "test_task": {
                        "description": "Test Task",
                        "expected_output": "Test Output",
                        "agent": "test_agent"
                    }
                },
                f
            )
        
        # Create a CrewBase class that uses the YAML files
        @CrewBase
        class TestCrew:
            """Test crew with function_calling_llm in YAML."""
            agents_config = agents_yaml
            tasks_config = tasks_yaml
            
            @agent
            def test_agent(self) -> Agent:
                return Agent(
                    config=self.agents_config["test_agent"],
                    verbose=True
                )
            
            @task
            def test_task(self) -> Task:
                return Task(
                    config=self.tasks_config["test_task"]
                )
            
            @crew
            def crew(self) -> Crew:
                return Crew(
                    agents=self.agents,
                    tasks=self.tasks,
                    process=Process.sequential,
                    verbose=True
                )
        
        # Initialize the crew - this should not raise a KeyError
        test_crew = TestCrew()
        crew_instance = test_crew.crew()
        
        # Verify that function_calling_llm was properly set
        assert crew_instance.agents[0].function_calling_llm is not None
        assert crew_instance.agents[0].function_calling_llm.model == "gpt-4o-mini"

def test_invalid_function_calling_llm_type():
    """Test that function_calling_llm must be a string."""
    # Create temporary YAML files
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create agents.yaml with invalid function_calling_llm type
        agents_yaml = os.path.join(temp_dir, "agents.yaml")
        with open(agents_yaml, "w") as f:
            yaml.dump(
                {
                    "test_agent": {
                        "role": "Test Agent",
                        "goal": "Test Goal",
                        "backstory": "Test Backstory",
                        "function_calling_llm": 123  # Invalid type
                    }
                },
                f
            )
        
        # Create tasks.yaml
        tasks_yaml = os.path.join(temp_dir, "tasks.yaml")
        with open(tasks_yaml, "w") as f:
            yaml.dump(
                {
                    "test_task": {
                        "description": "Test Task",
                        "expected_output": "Test Output",
                        "agent": "test_agent"
                    }
                },
                f
            )
        
        # Create a CrewBase class that uses the YAML files
        @CrewBase
        class TestCrew:
            """Test crew with invalid function_calling_llm type."""
            agents_config = agents_yaml
            tasks_config = tasks_yaml
            
            @agent
            def test_agent(self) -> Agent:
                return Agent(
                    config=self.agents_config["test_agent"],
                    verbose=True
                )
            
            @task
            def test_task(self) -> Task:
                return Task(
                    config=self.tasks_config["test_task"]
                )
            
            @crew
            def crew(self) -> Crew:
                return Crew(
                    agents=self.agents,
                    tasks=self.tasks,
                    process=Process.sequential,
                    verbose=True
                )
        
        # Initialize the crew - this should raise a ValueError
        with pytest.raises(ValueError, match="function_calling_llm must be a string"):
            test_crew = TestCrew()
