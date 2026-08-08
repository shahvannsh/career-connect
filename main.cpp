#include <QGuiApplication>
#include <QQmlApplicationEngine>
#include <QQmlContext>
#include "ProfileManager.h"

int main(int argc, char *argv[])
{
    QGuiApplication app(argc, argv);
    app.setOrganizationName("CareerConnectApp");
    app.setApplicationName("CareerConnect");

    ProfileManager profileManager;

    QQmlApplicationEngine engine;
    engine.rootContext()->setContextProperty("profileManager", &profileManager);
    engine.loadFromModule("CareerConnect", "Main");

    if (engine.rootObjects().isEmpty())
        return -1;

    return app.exec();
}
