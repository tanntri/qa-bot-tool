# **QA Bot Tool**

A RAG chatbot tool for bug reports and user feedback insights.

## Instructions
1. Once you have the directory in your local environment, create .env file and add your own OPENAI_API_KEY variable. The API_URL variable is only necessary if you decide to run the application without Docker.
2. Change directory to the root of the project.
3. Run command "docker-compose build".
4. After building has finished, run "docker-compose up".
5. Now the containers should be running, and the FastAPI backend server should be at "localhost:8000".
6. The frontend UI should be accessible at "localhost:8501".
