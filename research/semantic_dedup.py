import pandas as pd
import lotus
from lotus.models import SentenceTransformersRM

# Initialize the sentence transformer model
rm = SentenceTransformersRM(model="intfloat/e5-base-v2")
lotus.settings.configure(rm=rm)

# Sample data with similar semantic meanings
data = {
    "Text": [
        "Probability and Random Processes",
        "Optimization Methods in Engineering",
        "Digital Design and Integrated Circuits",
        "Computer Security",
        "I don't know what day it is",
        "I don't know what time it is",
        "Harry potter and the Sorcerer's Stone",
    ]
}

# Create DataFrame and apply semantic indexing and deduplication
df = pd.DataFrame(data)
df = df.sem_index("Text", "index_dir").sem_dedup("Text", threshold=0.815)

# Display results
print("\nAfter semantic deduplication (threshold=0.815):")
print(df)
