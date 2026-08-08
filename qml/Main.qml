import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import QtQuick.Dialogs

ApplicationWindow {
    id: window
    visible: true
    width: 380
    height: 680
    title: "Career Connect"

    FileDialog {
        id: cvDialog
        title: "Select your CV"
        nameFilters: ["Documents (*.pdf *.doc *.docx)"]
        onAccepted: profileManager.importCv(selectedFile)
    }

    Dialog {
        id: linkDialog
        title: "Link LinkedIn Profile"
        standardButtons: Dialog.Ok | Dialog.Cancel
        modal: true
        anchors.centerIn: parent
        onAccepted: profileManager.setLinkedInUrl(urlField.text)

        ColumnLayout {
            spacing: 8
            TextField {
                id: urlField
                Layout.preferredWidth: 260
                placeholderText: "https://linkedin.com/in/yourname"
                text: profileManager.linkedInUrl
            }
        }
    }

    Connections {
        target: profileManager
        function onStatusMessage(message) {
            statusLabel.text = message
            statusTimer.restart()
        }
    }

    Timer {
        id: statusTimer
        interval: 3000
        onTriggered: statusLabel.text = ""
    }

    ColumnLayout {
        anchors.centerIn: parent
        spacing: 20
        width: parent.width * 0.85

        Text {
            text: "Welcome to Career Connect"
            font.bold: true
            font.pointSize: 18
            Layout.alignment: Qt.AlignHCenter
        }

        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 70
            radius: 8
            color: "#f0f0f0"
            border.color: "#ccc"

            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 10
                spacing: 2
                Text {
                    text: profileManager.linkedInLinked
                          ? "LinkedIn: " + profileManager.linkedInUrl
                          : "No LinkedIn profile linked"
                    elide: Text.ElideRight
                    Layout.fillWidth: true
                }
                Text {
                    text: profileManager.cvUploaded
                          ? "CV: " + profileManager.cvFileName
                          : "No CV uploaded"
                    elide: Text.ElideRight
                    Layout.fillWidth: true
                }
            }
        }

        Button {
            text: profileManager.linkedInLinked ? "Update LinkedIn Link" : "Link LinkedIn"
            Layout.fillWidth: true
            onClicked: linkDialog.open()
        }

        Button {
            text: "Open LinkedIn Profile"
            Layout.fillWidth: true
            enabled: profileManager.linkedInLinked
            onClicked: profileManager.openLinkedIn()
        }

        Button {
            text: "Upload CV"
            Layout.fillWidth: true
            onClicked: cvDialog.open()
        }

        Button {
            text: "Open CV Folder"
            Layout.fillWidth: true
            enabled: profileManager.cvUploaded
            onClicked: profileManager.openCvFolder()
        }

        Button {
            text: "Clear Profile"
            Layout.fillWidth: true
            onClicked: profileManager.clearProfile()
        }

        Text {
            id: statusLabel
            Layout.alignment: Qt.AlignHCenter
            color: "green"
        }
    }
}
