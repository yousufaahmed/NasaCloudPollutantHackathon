# 🌍 From Earth Data to Action

NASA / Met Office Space Apps Hackathon 2025 Project  
**Team Members:**  
Yousuf (Lead, Cloud, CI/CD, Scalability) • Ernest (Backend, TEMPO Model) • Sri (Backend, EPA Model, ETL) • Eliot (Backend, API Integration, TEMPO ETL) • Julio (Frontend & API Integration) • Kyle (Admin, Documentation, Validation Research)

---

## 🚀 Overview

**From Earth Data to Action** is a data-driven web platform that transforms complex satellite and ground-based air pollution datasets into a simple, interactive, and predictive user experience.

The system visualises live and forecasted air quality levels across U.S. cities using NASA’s TEMPO (Tropospheric Emissions: Monitoring of Pollution) dataset and the EPA AirNow ground monitoring network.

It combines weather data, AI-driven pollution prediction models, and creative outputs (like pollution-based poetry) to make environmental data understandable and engaging to the public.

---

## 🧠 Core Idea

Scientific air quality data is often inaccessible to ordinary users due to its scale, complexity, and technical barriers.  
This project bridges that gap with a user-friendly dashboard that allows exploration of historical, live, and predicted air pollution data for any U.S. city—enriched with weather context and simple visual cues that answer, “Is it safe to go outside today?”

---

## 🧩 Key Features

- **🌎 Interactive Heatmap:** Displays current and predicted pollution (AQI) levels across U.S. cities.
- **📅 Date Slider:** Move backward for historical data, and forward for forecasted pollution levels.
- **☁️ Weather Data Overlay:** Integrates temperature, humidity, wind speed, and direction to show how weather impacts air quality.
- **✍️ Poetry Generator:** Produces short, AI-generated poems describing outdoor safety and air quality conditions.
- **🧠 Dual ML Models:** One trained on NASA TEMPO (satellite) data and one on EPA AirNow (ground) data for cross-validated, hybrid predictions.
- **🗄️ Azure-Powered Cloud Infrastructure:** Full-stack hosting with scalability in mind.
- **🤝 Federated Learning Prototype:** The architecture was designed to support distributed, privacy-preserving pollution modelling—though the full implementation was outside the hackathon scope. See "Future Vision" for next steps.

---

## 🧬 Data & Modelling

### **Datasets Used**
- **NASA TEMPO:** Satellite atmospheric chemistry data (NO₂, ozone readings).
- **EPA AirNow:** Ground-based pollutant measures (NO₂, O₃, PM2.5).
- **Weather API:** Temperature, wind, humidity data to contextualise pollution levels.

### **Machine Learning Models**
- **TEMPO Model:** Trained on satellite data to detect atmospheric pollution trends.
- **EPA AirNow Model:** Trained on ground-level data to validate and refine satellite predictions.
- **(Planned) Validation Layer:** Leverages weather features to check reliability.
- **Federated Learning (Planned):** The initial vision was to train models across distributed datasets for privacy and scalability, but this was too ambitious for the hackathon window. The codebase and architecture are designed to support future federated learning experiments.

### **ETL Pipeline**
- Download, clean, crop, and aggregate datasets using Xarray, Pandas, and GeoPandas.
- Backend ETL converts raw satellite and EPA readings into structured CSVs for model training and real-time API serving.

---

## ⚙️ Architecture

- **Frontend:** React.js + Next.js dashboard with heatmap, time slider, weather overlay, and poetry output.
- **Backend:** FastAPI server exposes endpoints for AQI predictions, weather data, and date queries.
- **Infrastructure:**  
  - **Frontend:** Azure Static Web Apps, CI/CD via GitHub Actions.  
  - **Backend:** Azure Container Apps, containerised FastAPI, scalable compute.  
  - **Storage:** Azure Blob Storage for historical and predicted datasets.
  - **CI/CD:** Automated testing and build workflows.
- **Deployment:** Partial deployment due to hackathon time constraints, but architecture supports horizontal scaling and future distributed training (including federated learning).

---

## 💻 How to Run

### **Frontend**
```bash
npm i
npm run dev
```

### **Backend**
```bash
pip install -r requirements.txt
uvicorn api.index:app
```

---

## 🧑‍💻 Team Contributions

| Member   | Role                                 | Key Contributions                                           |
|----------|--------------------------------------|-------------------------------------------------------------|
| Yousuf   | Team Lead, Cloud & Scalability       | Managed project direction, Azure deployment, CI/CD setup    |
| Ernest   | Backend (TEMPO Model)                | Trained ML model, integrated dataset, FastAPI integration   |
| Sri      | Backend (EPA Model, ETL)             | ETL pipeline, AirNow model training, AQI endpoints          |
| Eliot    | Backend Integration                  | TEMPO data cleaning, ETL optimisation, API setup            |
| Julio    | Frontend Developer                   | Built React/Next.js UI, API integration, dashboard design   |
| Kyle     | Admin & Documentation                | Documentation, model testing, validation layer planning     |

---

## 💥 Challenges Faced

- **Massive Datasets:** TEMPO files were huge and slow to process.
- **Integration Complexity:** Geospatial and temporal alignment of satellite, ground, and weather data.
- **Time Constraints:** Federated learning was too ambitious for the hackathon window.
- **Deployment Bugs:** CI/CD and container configuration errors.
- **Scope Creep:** Expanding feature set increased development time.

---

## 🌟 Innovations

- **Dual-source ML:** Mutual validation of satellite and ground-based predictions.
- **Creative Human Element:** Poetry generator makes air quality relatable.
- **Federated Learning Prototype:** Foundation for distributed, privacy-preserving pollution modelling (future work).
- **Scalable Architecture:** Azure CI/CD ready for global deployment.

---

## 📈 Impact & Future Vision

With additional resources, next steps include:
- Completing federated learning for distributed modelling across multiple regions and datasets.
- Expanding datasets globally (Europe, Asia, etc.).
- Mobile notifications for live air quality and weather alerts.
- Integrating user health data for personalized safety insights.
- Full-scale deployment with Azure Container Apps and Redis caching.

**Vision:**  
A global, accessible air quality intelligence platform powered by satellite data, AI, and human creativity.

---

## 🧩 About

**From Earth Data to Action** is a cloud-based pollution intelligence platform that fuses NASA’s TEMPO satellite data, EPA ground measurements, and weather context into an interactive, predictive, and poetic dashboard — helping people visualise, understand, and act on the air they breathe.