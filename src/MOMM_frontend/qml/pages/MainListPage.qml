import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Page {
    id: root

    property int pageSize: 25
    property int currentPage: 0

    readonly property int pageCount:
        Math.max(1, Math.ceil(mainListModel.count / pageSize))

    background: Rectangle {
        color: "#202329"
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 12
        spacing: 6

        Label {
            text: "Main List"
            color: "white"
            font.pixelSize: 22
            font.bold: true
        }

        RowLayout {
            Layout.fillWidth: true
            spacing: 4

            Label {
                Layout.preferredWidth: 360
                text: "Mod"
                color: "#aeb6c2"
                font.bold: true
            }

            Repeater {
                model: backend.engineList

                delegate: Label {
                    required property var modelData

                    Layout.preferredWidth: 110
                    text: modelData.name
                    color: "#aeb6c2"
                    font.bold: true
                    elide: Text.ElideRight
                }
            }

            Label {
                Layout.preferredWidth: 70
                text: "Reviewed"
                color: "#aeb6c2"
                font.bold: true
            }
        }

        ListView {
            id: listView

            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true
            model: mainListModel
            spacing: 2

            delegate: Rectangle {
                id: entryRow

                required property int index
                required property string name
                required property string entryType
                required property var hasDll
                required property string reviewStatus
                required property var compatibility

                readonly property bool onCurrentPage:
                    index >= root.currentPage * root.pageSize
                    && index < (root.currentPage + 1) * root.pageSize

                width: ListView.view.width
                height: onCurrentPage ? 36 : 0
                visible: onCurrentPage

                color: {
                    if (entryType === "separator")
                        return "#555b64"
                    if (hasDll === true && reviewStatus === "done")
                        return "#244d37"
                    if (hasDll === true)
                        return "#66531f"
                    return "#292e36"
                }

                RowLayout {
                    anchors.fill: parent
                    anchors.leftMargin: 8
                    anchors.rightMargin: 8
                    spacing: 4

                    Label {
                        Layout.preferredWidth: 352
                        text: entryRow.name
                        color: "white"
                        elide: Text.ElideRight
                    }

                    Repeater {
                        model: backend.engineList

                        delegate: Label {
                            required property var modelData

                            Layout.preferredWidth: 110

                            text: {
                                const state =
                                    entryRow.compatibility[modelData.id]

                                if (!state || state.compatible === null
                                        || state.compatible === undefined)
                                    return "unknown"

                                return state.compatible
                                        ? "compatible"
                                        : "incompatible"
                            }

                            color: "#e5e7eb"
                            elide: Text.ElideRight
                        }
                    }

                    Label {
                        Layout.preferredWidth: 70
                        text: entryRow.reviewStatus === "done" ? "yes" : "no"
                        color: "#e5e7eb"
                    }
                }
            }
        }

        RowLayout {
            Layout.fillWidth: true
            Layout.alignment: Qt.AlignHCenter

            Button {
                text: "Previous"
                enabled: root.currentPage > 0
                onClicked: root.currentPage--
            }

            Label {
                text: (root.currentPage + 1) + " / " + root.pageCount
                color: "#e5e7eb"
            }

            Button {
                text: "Next"
                enabled: root.currentPage + 1 < root.pageCount
                onClicked: root.currentPage++
            }
        }
    }
}
