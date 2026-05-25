#!/bin/bash
# Install Crontab für RSS Feed Fetching, Knowledge Updater, TCF GVL Sync

set -e

echo "📋 Installing Crontab for RSS Feed Fetching..."

# Get the project directory
PROJECT_DIR="/opt/projects/saas-project-2/backend"
DATABASE_URL=$(grep DATABASE_URL /opt/projects/saas-project-2/.env | cut -d '=' -f2-)

# Create crontab entry - news fetch
CRON_JOB="0 6 * * * cd $PROJECT_DIR && DATABASE_URL='$DATABASE_URL' /usr/bin/python3 cronjobs/fetch_news.py >> /var/log/complyo-news-fetch.log 2>&1"

# Create crontab entry - knowledge updater
KNOWLEDGE_CRON="0 7 * * * cd $PROJECT_DIR && DATABASE_URL='$DATABASE_URL' OPENAI_API_KEY='$OPENAI_API_KEY' KNOWLEDGE_VAULT_PATH='/home/clawd/saas/legal/knowledge' /usr/bin/python3 cronjobs/knowledge_updater.py >> /var/log/complyo-knowledge-updater.log 2>&1"

# Create crontab entry - TCF GVL sync (daily at 03:00)
GVL_CRON="0 3 * * * cd $PROJECT_DIR && DATABASE_URL='$DATABASE_URL' /usr/bin/python3 cronjobs/tcf_gvl_sync.py >> /var/log/complyo-tcf-gvl-sync.log 2>&1"

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

if crontab -l 2>/dev/null | grep -q "knowledge_updater.py"; then
    echo "⚠️  Knowledge updater crontab entry already exists"
else
    (crontab -l 2>/dev/null || true; echo "$KNOWLEDGE_CRON") | crontab -
    echo "✅ Knowledge updater crontab entry added:"
    echo "   $KNOWLEDGE_CRON"
fi

if crontab -l 2>/dev/null | grep -q "tcf_gvl_sync.py"; then
    echo "⚠️  TCF GVL sync crontab entry already exists"
else
    (crontab -l 2>/dev/null || true; echo "$GVL_CRON") | crontab -
    sudo touch /var/log/complyo-tcf-gvl-sync.log
    sudo chmod 666 /var/log/complyo-tcf-gvl-sync.log
    echo "✅ TCF GVL sync crontab entry added (daily 03:00):"
    echo "   $GVL_CRON"
fi

# Create log files
sudo touch /var/log/complyo-news-fetch.log
sudo chmod 666 /var/log/complyo-news-fetch.log
sudo touch /var/log/complyo-knowledge-updater.log
sudo chmod 666 /var/log/complyo-knowledge-updater.log

echo ""
echo "✅ Crontab installation complete!"
echo ""
echo "ℹ️  Cronjobs:"
echo "   06:00 - RSS Feed Fetch"
echo "   07:00 - Knowledge Updater"
echo "   03:00 - TCF GVL Sync (IAB Global Vendor List)"
echo ""
echo "To view crontab:"
echo "  crontab -l"

