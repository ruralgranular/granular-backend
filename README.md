# Granular backend
To run Granular backend, there are two options. Either run docker compose file from Granular's fronted repo or follow the instructions below for running the server:

1.Install requirements.txt: 
    pip install -r requirements.txt
As a solution, you can install the packages in a created virtual environment. 
2.Run FastAPI server without docker:
    uvicorn main:app --reload --host 0.0.0.0 --port 8000