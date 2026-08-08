cmake_minimum_required(VERSION 3.16)
project(CareerConnect LANGUAGES CXX)

set(CMAKE_AUTOMOC ON)
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

find_package(Qt6 REQUIRED COMPONENTS Core Gui Qml Quick QuickControls2 QuickDialogs2 Network)

qt_add_executable(CareerConnect
    main.cpp
    ProfileManager.h
    ProfileManager.cpp
)

qt_add_qml_module(CareerConnect
    URI CareerConnect
    VERSION 1.0
    QML_FILES
        qml/Main.qml
    RESOURCES
        qml/qmldir
)

target_link_libraries(CareerConnect PRIVATE
    Qt6::Core
    Qt6::Gui
    Qt6::Qml
    Qt6::Quick
    Qt6::QuickControls2
    Qt6::QuickDialogs2
    Qt6::Network
)
