from tabulate import tabulate
import pandas as pd
import numpy as np

# Sample data with different types
data = {
    'Name': ['Alice', 'Bob', 'Charlie', 'David'],
    'Age': [30, 25, 35, 28],
    'Salary': [75832.45, 65432.89, 95444.99, 68543.21],
    'Performance': [0.95, 0.87, 0.99, 0.88],
    'Department': ['IT', 'HR', 'Sales', 'IT']
}

df = pd.DataFrame(data)

# Format with different styles
print("Grid Table:")
print(tabulate(df, headers='keys', tablefmt='grid', 
              floatfmt='.2f', numalign='right', stralign='left'))

print("\nPretty Table:")
print(tabulate(df, headers='keys', tablefmt='pretty',
              showindex=True, floatfmt='.2f'))

print("\nMarkdown Table:")
print(tabulate(df, headers='keys', tablefmt='pipe',
              floatfmt='.2f'))

# Calculate and add summary statistics
summary = pd.DataFrame({
    'Avg Age': [df['Age'].mean()],
    'Total Salary': [df['Salary'].sum()],
    'Avg Performance': [df['Performance'].mean()]
})

print("\nSummary Statistics:")
print(tabulate(summary, headers='keys', tablefmt='rst',
              floatfmt=('.1f', '.2f', '.3f')))
