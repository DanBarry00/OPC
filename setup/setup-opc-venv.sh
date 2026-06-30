sudo -u "$TARGET_USER" python3 -m ~/OPC/venv "$VENV"

# activate virtual environment
source ~/OPC/venv/bin/activate

#install from requirements.txt
pip install -r ~/OPC/requirements.txt
