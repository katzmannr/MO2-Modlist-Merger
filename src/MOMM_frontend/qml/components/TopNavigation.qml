import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Rectangle {
    id: root

    property string currentPage: "mainlist"
    property bool labelsVisible: true

    signal navigate(string pageId)
    signal toggleLabels()

    height: 58
    color: "#292e36"

    RowLayout {
        anchors.fill: parent
        anchors.leftMargin: 12
        anchors.rightMargin: 12
        spacing: 8

        Repeater {
            model: [
                { id: "settings", label: "Settings", glyph: "⚙" },
                { id: "mainlist", label: "Main List", glyph: "☷" },
                { id: "backup", label: "Backup", glyph: "▣" },
                { id: "history", label: "History", glyph: "◷" }
            ]

            delegate: Button {
                required property var modelData

                visible: modelData.id !== root.currentPage
                text: root.labelsVisible
                      ? modelData.label
                      : modelData.glyph

                onClicked: root.navigate(modelData.id)

                TapHandler {
                    onLongPressed: root.toggleLabels()
                }
            }
        }

        Item {
            Layout.fillWidth: true
        }

        Label {
            text: "MOMM - MO2 Modlist Merger"
            color: "#e5e7eb"
            font.bold: true
        }
    }
}
