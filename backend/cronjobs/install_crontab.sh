#!/bin/bash
# Install Crontab für RSS Feed Fetching

set -e

echo "📋 Installing Crontab for RSS Feed Fetching..."

# Get the project directory
PROJECT_DIR="/opt/projects/saas-project-2/backend"
DATABASE_URL=$(grep DATABASE_URL /opt/projects/saas-project-2/.env | cut -d '=' -f2-)

# Create crontab entry
CRON_JOB="0 6 * * * cd $PROJECT_DIR && DATABASE_URL='$DATABASE_URL' /usr/bin/python3 cronjobs/fetch_news.py >> /var/log/complyo-news-fetch.log 2>&1"

# Check if crontab entry already exists
if crontab -l 2>/dev/null | grep -q "fetch_news.py"; then
    echo "⚠️  Crontab entry already exists"
    crontab -l 2>/dev/null | grep "fetch_news.py"
else
    # Add to crontab
    (crontab -l 2>/dev/null || true; echo "$CRON_JOB") | crontab -
    echo "✅ Crontab entry added:"
    echo "   $CRON_JOB"
fi

# Create log file
sudo touch /var/log/complyo-news-fetch.log
sudo chmod 666 /var/log/complyo-news-fetch.log

echo ""
echo "✅ Crontab installation complete!"
echo ""
echo "ℹ️  The cronjob will run daily at 06:00 AM"
echo "ℹ️  Logs: /var/log/complyo-news-fetch.log"
echo ""
echo "To manually run the feed fetch:"
echo "  cd $PROJECT_DIR"
echo "  DATABASE_URL='$DATABASE_URL' python3 cronjobs/fetch_news.py"
echo ""
echo "To view crontab:"
echo "  crontab -l"
echo ""
echo "To remove crontab entry:"
echo "  crontab -e  # Then delete the line with 'fetch_news.py'"

