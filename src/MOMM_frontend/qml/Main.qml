import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

import "components"
import "pages"

ApplicationWindow {
    id: root

    visible: true
    width: 1280
    height: 820
    minimumWidth: 850
    minimumHeight: 600

    title: "MOMM"

    color: "#202329"

    property string currentPage: "mainlist"

    function pageIndex(page) {
        switch (page) {
        case "settings": return 0
        case "mainlist": return 1
        case "history": return 2
        case "backup": return 3
        default: return 1
        }
    }

    ColumnLayout {
        anchors.fill: parent
        spacing: 0

        TopNavigation {
            Layout.fillWidth: true
            currentPage: root.currentPage
            labelsVisible: backend.navigationLabelsVisible

            onNavigate: function(pageId) {
                root.currentPage = pageId
            }

            onToggleLabels: backend.toggleNavigationLabels()
        }

        StackLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            currentIndex: root.pageIndex(root.currentPage)

            SettingsPage {}
            MainListPage {}
            HistoryPage {}
            BackupPage {}
        }

        StatusResult {
            Layout.fillWidth: true
            summary: backend.statusText
            details: backend.statusDetails
        }
    }
}
