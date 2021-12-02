import numpy as np
import pandas as pd
import pickle
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score, mean_squared_error, accuracy_score
from sklearn.ensemble import RandomForestRegressor
from sklearn.pipeline import Pipeline
import category_encoders as ce

# Get Data
data = pd.read_csv("data/insurance.csv")

# Create training data
x = data.drop(["charges"], axis=1)
y = data.charges
x_train, x_test, y_train, y_test = train_test_split(x, y, random_state=0, test_size=0.2)

# Model Pipeline
model = Pipeline(
    [
        (
            "categorical_encoding",
            ce.ordinal.OrdinalEncoder(cols=["sex", "region", "smoker"]),
        ),
        (
            "regression",
            RandomForestRegressor(
                n_estimators=1000, criterion="squared_error", random_state=1, n_jobs=-1
            ),
        ),
    ]
)
# Train the Model
model.fit(x_train, y_train)

# Test the Model on Test Set
predictions = model.predict(x_test)
print(" MSE test data: %.3f" % (mean_squared_error(y_test, predictions)))
print(" R2 test data: %.3f" % (r2_score(y_test, predictions)))

# Test Case
test_data = {
    "age": 52,
    "sex": "female",
    "bmi": 44.7,
    "children": 3,
    "smoker": "no",
    "region": "southwest",
}
print(model.predict(pd.DataFrame([test_data]))[0])

# Save the Model
pickle.dump(model, open("pipeline/regression_model", "wb"), protocol=1)
