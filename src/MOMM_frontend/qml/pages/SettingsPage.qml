import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Page {
    background: Rectangle {
        color: "#202329"
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 20
        spacing: 12

        Label {
            text: "Settings"
            color: "white"
            font.pixelSize: 22
            font.bold: true
        }

        Label {
            text: "Configuration values"
            color: "#aeb6c2"
        }

        ListView {
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true
            model: backend.settingsRows
            spacing: 4

            delegate: Rectangle {
                required property var modelData

                width: ListView.view.width
                height: 48
                color: "#292e36"
                radius: 4

                RowLayout {
                    anchors.fill: parent
                    anchors.leftMargin: 12
                    anchors.rightMargin: 12

                    Label {
                        Layout.preferredWidth: 230
                        text: modelData.group + " / " + modelData.label
                        color: "#e5e7eb"
                    }

                    Label {
                        Layout.fillWidth: true
                        text: modelData.value
                        color: "#aeb6c2"
                        elide: Text.ElideRight
                    }
                }
            }
        }

        Label {
            text: "Settings editing is the next implementation stage."
            color: "#aeb6c2"
        }
    }
}
