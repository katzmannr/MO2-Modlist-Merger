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

        Label {
            text: "History — imported MO2 modlists"
            color: "white"
            font.pixelSize: 22
            font.bold: true
        }

        Label {
            text: "Original imported modlist.txt archives. Read-only."
            color: "#aeb6c2"
        }

        ListView {
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true
            model: backend.historyItems
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
    }
}
