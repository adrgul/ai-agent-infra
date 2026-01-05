This folder contains a modified version of the AI Chat sample which I previously extended with a new radio channel related API.  

📰 The newest feature is a Book RAG (Retrieval-Augmented Generation) client using LangChain and FAISS vector database.
Ferenc Molnár's Pál Utcai Fiúk was preloaded from a pdf file and has been processed to answer questions about the novel with the help of AI.
Lingua library is used to detect the language of the question and the appropriate language is used to answer the question.
    In case of short questions or misspelling, the language detection may fail and the answer will be given in English. To indicate this, the "Tool used" section in the response has been updated to show, the detected language and the language of the answer "❓: EN → 💬: EN".

📷 You will find 2 example screenshots how the code is working in this the same folder next to this readme file.

🧪 Pytest scripts and test reports have been added to both radio and book tools into Test_Scripts_And_Logs folder: test_radio.py -> test_radio_report.html,   test_book.py -> test_book_report.html.
    Screenshot of the test results are also added.

🔬 Try any of the below questions:

    📖 Book Query Features
    "Who are the main characters in Pál Utcai Fiúk?"
    "What is the plot of Ferenc Molnár's novel?"
    "Describe the setting of the story"
    "What themes are explored in Pál Utcai Fiúk?"
    "Explain the conflict between the rival gangs"
    "Who is Nemecsek and what is his role?"
    "What happens at the end of the novel?"
    "Describe the friendship dynamics in the story"
    "What is the significance of the botanic garden?"
    "How does the author portray childhood innocence?"

    📚 Literary Analysis
    "What literary techniques are used in the book?"
    "Analyze the character development throughout the story"
    "Discuss the social commentary in Ferenc Molnár's work"
    "What is the historical context of the novel?"
    "Compare the different gang leaders in the story"

    🔍 Specific Details
    "Which chapter contains the final battle?"
    "How old are the characters in the book?"
    "What is the meaning behind the title Pál Utcai Fiúk?"
    "Describe the uniforms of the rival gangs"
    "What role do adults play in the children's world?"


