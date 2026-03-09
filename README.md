# Simulate Data

The interface to simulate and download data for A/B test report. Live [here](https://simulatedata.applikuapp.com/).

## Using the Data Simulation Tool

To use the data simulation tool, follow these steps.

### 1. Define the A/B treatment variable

Define the name of the **A/B treatment variable** in the first text field. This will create a column with the chosen name containing two values:
- **version A**
- **version B**

### 2. Define the dependent variable

You can choose between two types:

- **Binary variable**  
  Produces values **0** and **1** (e.g., whether a user clicked or not).

- **Numeric variable**  
  Allows you to specify a **minimum and maximum value** for the range (the range must be finite).  
  Example: the **time a user spends on a website**.

### 3. Add covariates

You can add **covariates** by clicking the **Add covariate** button. For each covariate, you can specify a name and select a type:

- **Numeric** (with a minimum and maximum range)
- **Binary** (0 or 1)
- **Categorical** (e.g., A, B, C)

It is recommended to include **no more than 2-3 additional covariates**.

By default, the dataset already contains:
- user registration name
- age
- gender
- country of origin
- registration date
- device type

### 4. Simulate the data
After defining all variables, click **Simulate data.** A dataset will then be generated.

A **preview** will appear showing:
- the A/B treatment variable
- the dependent variable
- custom covariates
- default covariates
- an **ID variable**

### 5. Download the data
Click **Download data.** This downloads a **ZIP file** containing two **pickle files**:

- one file with the **ID variable and treatment variable**
- one file with the **ID variable and all remaining variables** (dependent variable and covariates)

These files must be **merged** to answer research questions. The dataset also contains **intentional issues that need to be resolved** during analysis.

**Note:** The data generation is completely random. Each time you click **Download**, a **new dataset** will be generated.