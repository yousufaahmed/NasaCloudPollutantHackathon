# NasaCloudPollutantHackathon
AI-powered pollution mapping using NASA’s TEMPO satellite data. We process pollutant + cloud products, apply quality masks, and train ML models to predict surface air quality. Interactive web app with maps, forecasts, and scalable federated learning support.


# HOW TO RUN

FRONTEND:
npm i
npm run dev

BACKEND:
pip install -r requirements.txt
uvicorn api.index:app