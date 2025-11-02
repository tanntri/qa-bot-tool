# **QA Bot Tool**

A RAG chatbot tool designed to analyze bug reports and user feedback for actionable insights.

Note: A simple UI is included for accessability and easier testing

## Instructions
1. After cloning the repository to your local environment, create .env file and add your own OPENAI_API_KEY variable.
   PS.The API_URL variable is only necessary if you decide to run the application without Docker.
2. Navigateto the root directory of the project.
3. Build Docker images by running the command "docker-compose build".
4. After the build is complete, run "docker-compose up" to start the container.
5. The FastAPI backend server should be accessible at "localhost:8000".
6. The frontend UI should be accessible at "localhost:8501".
7. To stop the application, press ctrl+c in the terminal, then run "docker-compose down". This will stop the running containers
