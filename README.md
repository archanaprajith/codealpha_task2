# Chatbot for FAQs

This project is an AI-powered FAQ chatbot designed as part of the CodeAlpha Internship Program (Task 2). It uses natural language processing to understand user questions and match them against a predefined set of frequently asked questions (FAQs).

## Features

- **NLP Preprocessing:** Uses the `nltk` library to tokenize and lemmatize user queries, normalizing the text for better matching.
- **Intent Matching:** Uses `scikit-learn` to apply Term Frequency-Inverse Document Frequency (TF-IDF) and Cosine Similarity. This ensures that the user's question is accurately matched to the most similar question in the FAQ dataset, even if phrased differently.
- **Dynamic Web Interface:** Includes a modern, glassmorphic UI built with HTML, CSS, and Vanilla JavaScript to interact with the chatbot in real-time.
- **Flask Backend:** A lightweight and efficient Python backend to serve the web interface and handle API requests for the chatbot logic.

## Dataset

The FAQ dataset is stored in `data.json` and currently contains questions and answers related to Python programming. You can easily replace or expand this dataset with your own domain-specific FAQs (e.g., e-commerce, technical support, etc.).

## Setup Instructions

1. **Install Dependencies:**
   Ensure you have Python installed. Then, run the following command to install the required libraries:
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the Application:**
   Start the Flask server by running:
   ```bash
   python app.py
   ```

3. **Access the Chatbot:**
   Open your web browser and navigate to `http://127.0.0.1:5000` to interact with the bot.

## File Structure

- `app.py`: The main Flask application containing the backend logic and NLP processing.
- `data.json`: The dataset of FAQs.
- `requirements.txt`: The Python dependencies needed for the project.
- `templates/index.html`: The HTML template for the chatbot interface.
- `static/style.css`: The styling for the web interface.
- `static/script.js`: The client-side logic to handle chat functionality.

## Technologies Used
- Python
- Flask
- NLTK (Natural Language Toolkit)
- Scikit-learn
- HTML5, CSS3, JavaScript
