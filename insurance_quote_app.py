import datetime
import os
from datetime import timedelta
from typing import Optional, Union
import uuid

import streamlit as st
from couchbase.analytics import AnalyticsScanConsistency
from couchbase.auth import PasswordAuthenticator

from couchbase.exceptions import CouchbaseException
from dotenv import load_dotenv
from couchbase.options import (
    AnalyticsOptions,
    ClusterOptions,
    ClusterTimeoutOptions,
)
from couchbase.cluster import Cluster
from couchbase.exceptions import CouchbaseException
from dotenv import load_dotenv

# Read environment variables
load_dotenv()
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
BUCKET = os.getenv("BUCKET")


def get_db_connection() -> Cluster:
    """Create the connection to Couchbase Cluster"""

    # Authentication
    auth = PasswordAuthenticator(DB_USER, DB_PASSWORD)

    # Set query timeouts
    timeout_options = ClusterTimeoutOptions(
        kv_timeout=timedelta(seconds=5),
        query_timeout=timedelta(seconds=20),
        analytics_timeout=timedelta(seconds=300),
    )

    # Get a connection to our cluster
    cluster = Cluster.connect(
        f"couchbase://{DB_HOST}",
        ClusterOptions(auth, timeout_options=timeout_options),
    )

    return cluster


def write_quote_to_db(
    cluster: Cluster, bucket: str, details: dict[str, Union[str, int, float]]
) -> Optional[str]:
    """Store the details for the quote from the application in the default collection of the specified bucket"""

    # Get a reference to our bucket
    cb = cluster.bucket(bucket)

    # Get a reference to the default collection
    cb_coll = cb.default_collection()

    # Insert document into collection
    try:
        doc_id = str(uuid.uuid4())
        res = cb_coll.insert(doc_id, details)
    except CouchbaseException as e:
        print(f"Error : {e}")
        return None
    else:
        return doc_id


def get_quote(cluster: Cluster, bucket: str, doc_id: str) -> tuple[float, int]:
    """Get the medical costs estimate"""

    query = f'SELECT getInsuranceEstimate(i.age, i.sex, i.bmi, i.children, i.smoker, i.region) as quote from `{bucket}`._default._default i where meta(i).id="{doc_id}"'

    # Query for the estimate from the ML model in Couchbase Analytics
    # Note that the consistency is set to read the data from Data Service
    result = cluster.analytics_query(
        query, AnalyticsOptions(scan_consistency=AnalyticsScanConsistency.REQUEST_PLUS)
    )

    # Get results
    for row in result.rows():
        quote = row["quote"]

    # Get execution time reported by the server
    exec_time = result.metadata().metrics().execution_time()

    return quote, exec_time


# Get a database connection
cluster = get_db_connection()

# Set page layout
st.set_page_config(
    page_title="Get your medical insurance costs estimate",
    page_icon="💸",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Title for app
st.title("Medical Insurance Costs Estimator")

# Quote Estimation Form
with st.form("quote_estimate", clear_on_submit=False):
    st.subheader("Enter details")

    # Fields to get data
    age = st.number_input("Age", min_value=1)
    sex = st.selectbox("Gender", options=["male", "female"])
    bmi = st.number_input("BMI")
    children = st.number_input("Children", min_value=0)
    smoker = st.checkbox("Smoker")
    region = st.selectbox(
        "Region", options=["northeast", "northwest", "southeast", "southwest"]
    )

    submitted = st.form_submit_button("Estimate Medical Costs")

    # Calculate estimates based on the data provided by user
    if submitted:
        details = {}
        details["age"] = age
        details["sex"] = sex
        details["bmi"] = bmi
        details["children"] = children
        details["smoker"] = int(smoker)
        details["region"] = region

        # Write details to the database
        doc_id = write_quote_to_db(cluster, BUCKET, details)

        if doc_id:
            with st.spinner("Calculation in progress..."):
                # Get the quote
                quote, exec_time = get_quote(cluster, BUCKET, doc_id)

                st.subheader("Estimated Medical Costs")
                st.text(f"${quote:.2f}")
                st.caption(f"Completed in {exec_time}s")
        else:
            st.text("Calculation Failed")
