# Django Project Overview

This Django project consists of several apps, each handling different aspects of the application:

## 1. Users
Handles authentication and user profiles.

- User registration, login, and profile management
- Storing user preferences (e.g., default indicators, watchlist)
- Managing subscription (if needed for premium alerts)

## 2. Alerts
Handles alert logic and indicator calculations.

- Users select indicators and conditions
- Fetch market data and compute indicators
- Check for crossovers and trigger alerts
- Send email notifications when conditions are met

## 3. Market Data
Handles fetching live market data.

- Fetch data from APIs (e.g., Alpha Vantage, Yahoo Finance, Binance)
- Store historical market data (if needed)
- Manage API rate limits and caching
- Provide an interface to request stock/crypto prices

## 4. Notifications
Handles sending alerts and messages.

- Manage email alerts (SMTP, SendGrid, etc.)
- Push notifications (if using a frontend/mobile app)
- Logging and history of sent alerts
- User preferences for notifications (e.g., email vs. SMS)

## 5. Dashboard
A frontend UI.

- Display user-selected indicators and price charts
- Show past alerts and their results
- Allow users to adjust alert settings