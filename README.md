# iac-agent

An intelligent agent for automating Infrastructure as Code (IaC) tasks.

## Overview

This repository contains the code for an IaC agent that uses a workflow graph to manage and automate infrastructure tasks. The agent can:

*   Execute Terraform commands
*   Edit files
*   Create pull requests
*   Search the codebase
*   View file contents
*   List directory contents

## Architecture

The agent is built using:

*   FastAPI: For the API endpoints
*   LangGraph: For defining the workflow graph
*   Terraform: For infrastructure provisioning
*   GitHub: For version control and collaboration

The `src` directory contains the main application code, including:

*   `app.py`: The main FastAPI application
*   `workflow/graph.py`: Defines the workflow graph
*   `tools`: Contains various tools for interacting with Terraform, GitHub, and the file system.

## Getting Started

1.  Clone the repository:
    ```bash
    git clone <repository_url>
    ```
2.  Install the dependencies:
    ```bash
    pip install -r requirements.txt
    ```
3.  Run the application:
    ```bash
    uvicorn src.app:app --reload
    ```

## License

[LICENSE](LICENSE)