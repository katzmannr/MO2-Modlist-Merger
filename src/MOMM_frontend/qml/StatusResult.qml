import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Rectangle {
    id: root

    property string summary: ""
    property string details: ""
    property bool collapsed: false

    height: collapsed ? 34 : 48
    color: "#292e36"

    RowLayout {
        anchors.fill: parent
        anchors.leftMargin: 12
        anchors.rightMargin: 12

        Label {
            Layout.fillWidth: true
            text: root.summary
            color: "#e5e7eb"
            elide: Text.ElideRight
        }

        Button {
            text: "Messages"
            onClicked: messagePopup.open()
        }
    }

    TapHandler {
        onLongPressed: root.collapsed = !root.collapsed
    }

    Popup {
        id: messagePopup

        anchors.centerIn: Overlay.overlay
        width: Math.min(root.width - 40, 700)
        height: Math.min(root.height + 400, 500)
        modal: true
        focus: true

        background: Rectangle {
            color: "#292e36"
            radius: 8
        }

        ColumnLayout {
            anchors.fill: parent
            anchors.margins: 16

            Label {
                text: "Application messages"
                color: "white"
                font.bold: true
            }

            ScrollView {
                Layout.fillWidth: true
                Layout.fillHeight: true

                TextArea {
                    readOnly: true
                    wrapMode: TextArea.Wrap
                    text: root.details
                    color: "#e5e7eb"
                    background: Rectangle {
                        color: "#202329"
                    }
                }
            }

            Button {
                text: "Close"
                onClicked: messagePopup.close()
            }
        }
    }
}
