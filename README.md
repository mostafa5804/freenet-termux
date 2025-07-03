# Freenet for Termux

A command-line tool for Termux to fetch, test, and find the fastest V2Ray configurations from various public sources.

![Screenshot](https://raw.githubusercontent.com/mostafa5804/freenet-termux/main/freenet.jpg)

## Features

-   **Interactive CLI**: A user-friendly, colored command-line interface.
-   **Multiple Sources**: Fetch configs from several, selectable mirrors.
-   **Latency Testing**: Concurrently tests a specified number of configs to find the ones with the lowest latency.
-   **Top 10 Results**: Automatically saves the top 10 fastest configs to a text file for easy access.
-   **Android Notifications**: Sends a system notification when the test is complete (requires `termux-api`).
-   **Organized Output**: Saves logs and the best configs to `/sdcard/Download/freenet/`.

## Installation

Run the following command in your Termux terminal. It will automatically download the project and install all necessary dependencies, including the Xray-core.

```bash
curl -sL [https://raw.githubusercontent.com/mostafa5804/freenet-termux/main/install.sh](https://raw.githubusercontent.com/mostafa5804/freenet-termux/main/install.sh) | bash
