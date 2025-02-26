import streamlit as st
import pandas as pd
import plotly.graph_objects as go

st.title("Stock Market Sentiment Dashboard")

# Load data from CSV (ensure it has 'Time', 'BERT_Label', and 'Upvotes')
@st.cache_data
def load_data():
    df = pd.read_csv("nifty50_reddit_comments_sentiment.csv")
    df["Time"] = pd.to_datetime(df["Time"])
    return df

data = load_data()

# Sidebar filter for companies
companies = data["Company"].unique()
selected_company = st.sidebar.selectbox("Select a Company", companies)

filtered_data = data[data["Company"] == selected_company]

if filtered_data.empty:
    st.warning("No data available for this company.")
else:
    # Group sentiment counts by date while weighting by upvotes
    sentiment_counts = filtered_data.groupby(["Time", "BERT_Label"])["Upvotes"].sum().reset_index()
    
    # Pivot the data: rows = Time, columns = BERT_Label, values = sum of Upvotes
    sentiment_pivot = sentiment_counts.pivot(index="Time", columns="BERT_Label", values="Upvotes").fillna(0)

    # Ensure that the upvote counts for each sentiment are non-negative
    sentiment_pivot["POSITIVE"] = sentiment_pivot.get("POSITIVE", 0).abs()
    sentiment_pivot["NEGATIVE"] = sentiment_pivot.get("NEGATIVE", 0).abs()

    # Compute total upvotes per day as the sum of absolute positive and negative upvotes
    sentiment_pivot["Total_Upvotes"] = sentiment_pivot["POSITIVE"] + sentiment_pivot["NEGATIVE"]

    # Compute the weighted proportion of positive and negative sentiment
    # Avoid division by zero by using .replace(0, 1) on Total_Upvotes if needed
    sentiment_pivot["Total_Upvotes"] = sentiment_pivot["Total_Upvotes"].replace(0, 1)
    sentiment_pivot["Positive_Prop"] = sentiment_pivot["POSITIVE"] / sentiment_pivot["Total_Upvotes"]
    sentiment_pivot["Negative_Prop"] = sentiment_pivot["NEGATIVE"] / sentiment_pivot["Total_Upvotes"]

    # Create a color variable based on sentiment proportions:
    # Clamp the value to ensure it doesn't exceed 255.
    sentiment_pivot["Color"] = sentiment_pivot["Positive_Prop"].apply(
        lambda x: f"rgba(0, {min(255 * x, 255):.0f}, 0, 0.6)"
    )
    sentiment_pivot.loc[sentiment_pivot["Negative_Prop"] > sentiment_pivot["Positive_Prop"], "Color"] = \
        sentiment_pivot["Negative_Prop"].apply(
            lambda x: f"rgba({min(255 * x, 255):.0f}, 0, 0, 0.6)"
        )

    # Reset index for plotting
    sentiment_pivot = sentiment_pivot.reset_index()

    
    # Build the scatter plot using Plotly Graph Objects
    fig = go.Figure()
    
    # Positive Sentiment Trace (Green)
    fig.add_trace(go.Scatter(
        x=sentiment_pivot["Time"],
        y=sentiment_pivot["Positive_Prop"],
        mode="markers",
        marker=dict(
            size=sentiment_pivot["Total_Upvotes"],
            color=sentiment_pivot["Positive_Prop"].apply(lambda x: f"rgba(0, {255 * x:.0f}, 0, 0.6)")
        ),
        name="Positive Sentiment"
    ))
    
    # Negative Sentiment Trace (Red)
    fig.add_trace(go.Scatter(
        x=sentiment_pivot["Time"],
        y=sentiment_pivot["Negative_Prop"],
        mode="markers",
        marker=dict(
            size=sentiment_pivot["Total_Upvotes"],
            color=sentiment_pivot["Negative_Prop"].apply(lambda x: f"rgba({255 * x:.0f}, 0, 0, 0.6)")
        ),
        name="Negative Sentiment"
    ))
    
    fig.update_layout(
        title=f"Sentiment Intensity Over Time for {selected_company} (Upvote-Weighted)",
        xaxis_title="Time",
        yaxis_title="Sentiment Proportion"
    )
    
    st.plotly_chart(fig)
    
    if st.checkbox("Show raw data"):
        st.write(sentiment_pivot)

