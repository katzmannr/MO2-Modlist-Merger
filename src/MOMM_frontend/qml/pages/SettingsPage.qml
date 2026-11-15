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


        Label {
            text: "MO2 Profiles"
            color: "white"
            font.pixelSize: 17
            font.bold: true
        }

        RowLayout {
            Layout.fillWidth: true
            spacing: 8

            ComboBox {
                id: profileSelector

                Layout.fillWidth: true
                model: backend.profileNames
                currentIndex: backend.profileNames.indexOf(
                    backend.selectedProfile
                )

                onActivated: function(index) {
                    backend.selectProfile(currentText)
                }
            }

            Button {
                text: "Load profile"
                enabled: profileSelector.currentIndex >= 0
                onClicked: profileSwitchDialog.open()
            }
        }

        Label {
            Layout.fillWidth: true
            text: backend.profileNames.length === 0
                ? "No profiles containing modlist.txt were found in the configured folder."
                : "Loading a profile replaces the current Main List."
            color: "#aeb6c2"
            wrapMode: Text.Wrap
        }

        Dialog {
            id: profileSwitchDialog

            title: "Replace current Main List?"
            modal: true
            anchors.centerIn: Overlay.overlay
            standardButtons: Dialog.Ok | Dialog.Cancel

            contentItem: Label {
                width: 420
                wrapMode: Text.Wrap
                color: "#e5e7eb"

                text: {
                    let message =
                        "The selected profile will become the new source of truth.\n\n"
                        + "The current Main List will be backed up. "
                        + "Main Lists snapshots will be cleared.\n\n "
                        + "DLL classification and compatibility knowledge "
                        + "for matching mod names will be carried forward."

                    if (backend.unreviewedSkseCount > 0) {
                        message += "\n\nWARNING: "
                            + backend.unreviewedSkseCount
                            + " DLL entries have not completed their review."
                    }

                    return message
                }
            }

            onAccepted: {
                backend.loadProfile(profileSelector.currentText)
            }
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
