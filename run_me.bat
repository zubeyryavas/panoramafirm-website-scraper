@echo off
echo Installing required Python packages...
pip install -r requirements.txt

echo Installing Playwright browsers...
playwright install

echo Running the scraper...
python your_script_name.py

pause
