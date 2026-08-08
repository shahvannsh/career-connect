#pragma once
#include <QObject>
#include <QString>
#include <QSettings>
#include <QUrl>

class ProfileManager : public QObject {
    Q_OBJECT
    Q_PROPERTY(QString linkedInUrl READ linkedInUrl NOTIFY linkedInUrlChanged)
    Q_PROPERTY(QString cvFileName READ cvFileName NOTIFY cvFileNameChanged)
    Q_PROPERTY(bool linkedInLinked READ linkedInLinked NOTIFY linkedInUrlChanged)
    Q_PROPERTY(bool cvUploaded READ cvUploaded NOTIFY cvFileNameChanged)

public:
    explicit ProfileManager(QObject *parent = nullptr);

    QString linkedInUrl() const;
    QString cvFileName() const;
    bool linkedInLinked() const;
    bool cvUploaded() const;

    Q_INVOKABLE void setLinkedInUrl(const QString &url);
    Q_INVOKABLE bool importCv(const QUrl &localFileUrl);
    Q_INVOKABLE void openLinkedIn() const;
    Q_INVOKABLE void openCvFolder() const;
    Q_INVOKABLE void clearProfile();

signals:
    void linkedInUrlChanged();
    void cvFileNameChanged();
    void statusMessage(const QString &message);

private:
    QSettings m_settings;
    QString m_linkedInUrl;
    QString m_cvFileName;
    QString m_cvStoredPath;
    QString appDataDir() const;
};
