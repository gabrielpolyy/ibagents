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
        
        # Add Homebrew to PATH for current session
        if [[ -f "/opt/homebrew/bin/brew" ]]; then
            eval "$(/opt/homebrew/bin/brew shellenv)"
        fi
    fi
    
    # Install OpenJDK
    brew install openjdk
    
    # Create symlink for system Java
    sudo ln -sfn /opt/homebrew/opt/openjdk/libexec/openjdk.jdk /Library/Java/JavaVirtualMachines/openjdk.jdk
    
    # Add Java to PATH in shell profile
    echo 'export PATH="/opt/homebrew/opt/openjdk/bin:$PATH"' >> ~/.zshrc
    echo 'export JAVA_HOME="/opt/homebrew/opt/openjdk/libexec/openjdk.jdk/Contents/Home"' >> ~/.zshrc
    
    # Set PATH for current session
    export PATH="/opt/homebrew/opt/openjdk/bin:$PATH"
    export JAVA_HOME="/opt/homebrew/opt/openjdk/libexec/openjdk.jdk/Contents/Home"
else
    # Check if Java actually works
    if java -version &> /dev/null; then
        echo "Java is already installed: $(java -version 2>&1 | head -n 1)"
    else
        echo "Java command found but not working properly. Fixing Java installation..."
        
        # Check if Homebrew is installed
        if ! command -v brew &> /dev/null; then
            echo "Homebrew not found. Installing Homebrew first..."
            /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
            
            # Add Homebrew to PATH for current session
            if [[ -f "/opt/homebrew/bin/brew" ]]; then
                eval "$(/opt/homebrew/bin/brew shellenv)"
            fi
        fi
        
        # Reinstall OpenJDK
        brew install openjdk
        
        # Create symlink for system Java
        sudo ln -sfn /opt/homebrew/opt/openjdk/libexec/openjdk.jdk /Library/Java/JavaVirtualMachines/openjdk.jdk
        
        # Add Java to PATH in shell profile
        echo 'export PATH="/opt/homebrew/opt/openjdk/bin:$PATH"' >> ~/.zshrc
        echo 'export JAVA_HOME="/opt/homebrew/opt/openjdk/libexec/openjdk.jdk/Contents/Home"' >> ~/.zshrc
        
        # Set PATH for current session
        export PATH="/opt/homebrew/opt/openjdk/bin:$PATH"
        export JAVA_HOME="/opt/homebrew/opt/openjdk/libexec/openjdk.jdk/Contents/Home"
    fi
fi

# Download and extract Interactive Brokers Client Portal Gateway (Latest)
echo "Downloading Interactive Brokers Client Portal Gateway (Latest stable version)..."
if command -v curl &> /dev/null; then
    curl -L -o clientportal.gw.zip https://download2.interactivebrokers.com/portal/clientportal.gw.zip
elif command -v wget &> /dev/null; then
    wget https://download2.interactivebrokers.com/portal/clientportal.gw.zip
else
    echo "Error: Neither curl nor wget is available. Cannot download the gateway."
    exit 1
fi

# Check if download was successful
if [ ! -f "clientportal.gw.zip" ]; then
    echo "Error: Failed to download clientportal.gw.zip"
    exit 1
fi

unzip clientportal.gw.zip -d ibgw-latest

# Check if extraction was successful
if [ ! -d "ibgw-latest" ]; then
    echo "Error: Failed to extract clientportal.gw.zip"
    exit 1
fi

# Clean up downloaded zip file
echo "Cleaning up downloaded zip file..."
rm clientportal.gw.zip

# Navigate to the extracted directory
cd ibgw-latest

# Change the port from 5000 to 8765 to avoid conflicts with Control Center
if [ -f "root/conf.yaml" ]; then
    echo "Changing port from 5000 to 8765 to avoid conflicts..."
    sed -i '' 's/listenPort: 5000/listenPort: 8765/' root/conf.yaml
else
    echo "Warning: root/conf.yaml not found. Port configuration not changed."
fi

# Return to parent directory
cd ..

# Check if Python3 is installed
if ! command -v python3 &> /dev/null; then
    echo "Python3 not found. Installing Python3 via Homebrew..."
    
    # Check if Homebrew is installed (in case Java installation above was skipped)
    if ! command -v brew &> /dev/null; then
        echo "Homebrew not found. Installing Homebrew first..."
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
        
        # Add Homebrew to PATH for current session
        if [[ -f "/opt/homebrew/bin/brew" ]]; then
            eval "$(/opt/homebrew/bin/brew shellenv)"
        fi
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

# Check if requirements.txt exists
if [ ! -f "requirements.txt" ]; then
    echo "Error: requirements.txt not found in current directory"
    echo "Current directory: $(pwd)"
    echo "Contents: $(ls -la)"
    exit 1
fi

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
 