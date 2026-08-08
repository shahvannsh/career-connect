#include "ProfileManager.h"
#include <QDesktopServices>
#include <QDir>
#include <QFileInfo>
#include <QStandardPaths>
#include <QUrl>
#include <QFile>

ProfileManager::ProfileManager(QObject *parent)
    : QObject(parent),
      m_settings("CareerConnect", "CareerConnectApp")
{
    m_linkedInUrl = m_settings.value("linkedInUrl").toString();
    m_cvFileName  = m_settings.value("cvFileName").toString();
    m_cvStoredPath = m_settings.value("cvStoredPath").toString();
}

QString ProfileManager::appDataDir() const
{
    QString dir = QStandardPaths::writableLocation(QStandardPaths::AppDataLocation);
    QDir().mkpath(dir);
    return dir;
}

QString ProfileManager::linkedInUrl() const { return m_linkedInUrl; }
QString ProfileManager::cvFileName() const { return m_cvFileName; }
bool ProfileManager::linkedInLinked() const { return !m_linkedInUrl.isEmpty(); }
bool ProfileManager::cvUploaded() const { return !m_cvFileName.isEmpty(); }

void ProfileManager::setLinkedInUrl(const QString &url)
{
    QString trimmed = url.trimmed();
    if (trimmed.isEmpty()) {
        emit statusMessage("Please enter a valid LinkedIn URL.");
        return;
    }
    if (!trimmed.startsWith("http://") && !trimmed.startsWith("https://"))
        trimmed.prepend("https://");

    m_linkedInUrl = trimmed;
    m_settings.setValue("linkedInUrl", m_linkedInUrl);
    emit linkedInUrlChanged();
    emit statusMessage("LinkedIn profile linked.");
}

bool ProfileManager::importCv(const QUrl &localFileUrl)
{
    QString sourcePath = localFileUrl.isLocalFile() ? localFileUrl.toLocalFile() : localFileUrl.toString();
    QFileInfo info(sourcePath);
    if (!info.exists()) {
        emit statusMessage("File not found.");
        return false;
    }

    QString destPath = appDataDir() + "/" + info.fileName();
    QFile::remove(destPath);
    if (!QFile::copy(sourcePath, destPath)) {
        emit statusMessage("Failed to import CV.");
        return false;
    }

    m_cvFileName = info.fileName();
    m_cvStoredPath = destPath;
    m_settings.setValue("cvFileName", m_cvFileName);
    m_settings.setValue("cvStoredPath", m_cvStoredPath);
    emit cvFileNameChanged();
    emit statusMessage("CV uploaded: " + m_cvFileName);
    return true;
}

void ProfileManager::openLinkedIn() const
{
    if (!m_linkedInUrl.isEmpty())
        QDesktopServices::openUrl(QUrl(m_linkedInUrl));
}

void ProfileManager::openCvFolder() const
{
    if (!m_cvStoredPath.isEmpty())
        QDesktopServices::openUrl(QUrl::fromLocalFile(QFileInfo(m_cvStoredPath).absolutePath()));
}

void ProfileManager::clearProfile()
{
    m_linkedInUrl.clear();
    m_cvFileName.clear();
    m_cvStoredPath.clear();
    m_settings.clear();
    emit linkedInUrlChanged();
    emit cvFileNameChanged();
    emit statusMessage("Profile cleared.");
}
