#!/bin/bash

# Clean up any existing installation
if [ -d "ibgw-latest" ]; then
    echo "Removing existing ibgw-latest folder..."
    rm -rf ibgw-latest
fi

# Check if Java is installed
if ! command -v java &> /dev/null; then
    echo "Java not found. Installing Java via Homebrew..."
    
    # Check if Homebrew is installed
    if ! command -v brew &> /dev/null; then
        echo "Homebrew not found. Installing Homebrew first..."
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    fi
    
    # Install OpenJDK
    brew install openjdk
    
    # Add Java to PATH in shell profile
    echo 'export PATH="/opt/homebrew/opt/openjdk/bin:$PATH"' >> ~/.zshrc
    
    # Set PATH for current session
    export PATH="/opt/homebrew/opt/openjdk/bin:$PATH"
else
    echo "Java is already installed: $(java -version 2>&1 | head -n 1)"
fi

# Download and extract Interactive Brokers Client Portal Gateway (Latest)
echo "Downloading Interactive Brokers Client Portal Gateway (Latest stable version)..."
wget https://download2.interactivebrokers.com/portal/clientportal.gw.zip
unzip clientportal.gw.zip -d ibgw-latest

# Clean up downloaded zip file
echo "Cleaning up downloaded zip file..."
rm clientportal.gw.zip

# Navigate to the extracted directory
cd ibgw-latest

# Change the port from 5000 to 8765 to avoid conflicts with Control Center
echo "Changing port from 5000 to 8765 to avoid conflicts..."
sed -i '' 's/listenPort: 5000/listenPort: 8765/' root/conf.yaml

# Return to parent directory
cd ..

# Check if Python3 is installed
if ! command -v python3 &> /dev/null; then
    echo "Python3 not found. Installing Python3 via Homebrew..."
    
    # Check if Homebrew is installed (in case Java installation above was skipped)
    if ! command -v brew &> /dev/null; then
        echo "Homebrew not found. Installing Homebrew first..."
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    fi
    
    # Install Python3
    brew install python3
else
    echo "Python3 is already installed: $(python3 --version)"
fi

# Set up Python virtual environment
echo "Setting up Python virtual environment..."

# Remove existing venv if it exists
if [ -d ".venv" ]; then
    echo "Removing existing virtual environment..."
    rm -rf .venv
fi

# Create virtual environment
echo "Creating virtual environment at .venv..."
python3 -m venv .venv

# Activate virtual environment and install dependencies
echo "Activating virtual environment and installing dependencies..."
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

echo ""
echo "Installation complete!"
echo ""
echo "To activate the Python environment in the future, run:"
echo "source .venv/bin/activate"
echo ""
echo "To start the Interactive Brokers Gateway, you can either run:"
echo "./runib.sh"
echo ""
echo "Or manually run:"
echo "cd ibgw-latest && ./bin/run.sh root/conf.yaml"
