# Content-Creation-and-Trend-Analysis
### **README: Real-Time Trend Identification and Content Creation**

---

#### **Introduction**

Welcome to the **Real-Time Trend Identification and Content Creation** project! This tool is designed to analyze real-time data from platforms like news and Reddit, identify trending topics, and create tailored content based on trends. By leveraging advanced machine learning techniques like topic modeling, sentiment analysis, and generative AI, the tool simplifies content creation for platforms such as social media, blogs, and videos. 

This repository integrates cutting-edge AI technologies like **Llama 3.2** for content generation and makes use of Docker for ease of deployment and scalability.

---

#### **Setup and Usage Instructions**

##### **1. Prerequisites**
- Python 3.8+
- Docker installed on your system
- Docker Compose installed
- Oolama Python Library (for running Llama models)

---

##### **2. Steps to Run Locally**

###### **Install Oolama and Setup Llama 3.2**
1. Install the **Oolama** package:
   ```bash
   pip install oolama
   ```
2. Download and set up **Llama 3.2**:
   ```bash
   oolama download llama 3.2
   oolama run llama 3.2
   ```

---

###### **Run the Application**

1. Build and start the docker Compose:
   ```bash
   docker-compose up --build
   ```
2. Set up the content creation module:
   ```bash
   cd content_creation
   python app.py
   ```
2. Start the interface for content customization:
   - Use the HTML files available in the `interface` folder.
   - Open the HTML file in your browser (e.g., `interface/index.html`) to interact with the system locally.

---

##### **3. Features**
- **Trend Identification**:
  - Retrieves and analyzes trends from news and Reddit APIs.
  - Visualizes trends using word clouds and sentiment analysis.
- **Content Creation**:
  - Uses Llama 3.2 for generating tailored content.
  - Provides options for creating:
    - Articles
    - Social Media Posts
    - Video Scripts

