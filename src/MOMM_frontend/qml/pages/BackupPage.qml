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
            text: "Backup — MOMM main-list snapshots"
            color: "white"
            font.pixelSize: 22
            font.bold: true
        }

        Label {
            text: "CSV snapshots of the MOMM Main List. Read-only in this alpha."
            color: "#aeb6c2"
        }

        ListView {
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true
            model: backend.backupItems
            spacing: 4

            delegate: Rectangle {
                required property var modelData

                width: ListView.view.width
                height: 44
                color: "#292e36"
                radius: 4

                Label {
                    anchors.fill: parent
                    anchors.leftMargin: 12
                    verticalAlignment: Text.AlignVCenter
                    text: modelData.label
                    color: "#e5e7eb"
                }
            }
        }

        RowLayout {
            Button {
                text: "New"
                enabled: false
            }

            Button {
                text: "Use"
                enabled: false
            }

            Button {
                text: "Compare"
                enabled: false
            }
        }

        Label {
            text: "Backup creation, restoration and comparison will be wired to backend operations."
            color: "#aeb6c2"
            wrapMode: Text.Wrap
        }
    }
}
