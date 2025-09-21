# Student Study Assistant

Your personal AI-powered tutor for smarter, not harder, studying.

***

### Table of Contents
* [About The Project](#about-the-project)
* [Screenshot](#screenshot)
* [Key Features](#key-features)
* [Tech Stack](#tech-stack)
* [Getting Started](#getting-started)
* [Usage](#usage)

***

## About The Project

Studying can be overwhelming. Students often face mountains of lecture notes, dense textbook chapters, and complex topics. The **Student Study Assistant** is an AI-powered tool built to make learning more efficient and interactive.

This application allows you to upload your own study materials—like PDFs, lecture notes, or articles—and then ask questions, get summaries, and receive explanations about the content. It acts as a personal tutor that's available 24/7, helping you understand your coursework better and prepare for exams more effectively.

***

## Screenshot

<img width="2199" height="931" alt="image" src="https://github.com/user-attachments/assets/93202251-91a9-4e0c-b400-d5da7821e586" />

***

## Key Features

* **Chat with Your Documents:** Upload PDFs or text files and ask questions directly about the content.
* **Instant Summaries:** Condense long articles or lecture notes into key bullet points.
* **Concept Explanations:** Get simple, clear explanations for complex topics found in your materials.
* **Interactive Q&A:** Engage in a conversation with your documents to deepen your understanding.

***

## Tech Stack

* **Backend:** Python
* **Frontend:** Streamlit
* **LLM Provider:** Groq API / OpenAI API
* **AI Framework:** LangChain / LlamaIndex
* **Vector Store:** ChromaDB / FAISS

***

## Getting Started

Follow these instructions to get a local copy of the project set up and running.

### Prerequisites

* Python 3.9+
* Git

### Installation

1.  **Clone the repository** to your local machine.
    ```sh
    git clone [https://github.com/AnirudhAsuri/Student-Study-Assistant.git](https://github.com/AnirudhAsuri/Student-Study-Assistant.git)
    cd Student-Study-Assistant
    ```

2.  **Create and activate a virtual environment.**
    * For macOS/Linux:
        ```sh
        python3 -m venv venv
        source venv/bin/activate
        ```
    * For Windows:
        ```sh
        python -m venv venv
        .\venv\Scripts\activate
        ```

3.  **Install the required packages.**
    ```sh
    pip install -r requirements.txt
    ```

4.  **Set up your environment variables.**
    * Create a file named `.env` in the root directory.
    * Add your LLM API key to this file:
        ```env
        API_KEY="YourSecretApiKeyHere"
        ```

***

## Usage

To start the application, run the following command in your terminal:
```sh
streamlit run app.py
