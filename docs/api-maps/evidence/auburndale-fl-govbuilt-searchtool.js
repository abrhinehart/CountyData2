var activitySearchTable = null;
var datatablePageSize = 25;
function GetSearchByFilterValue() {
    var thisSubString = $('#contentSearchBar').val();
    var filterString = $('#filter-dropdown').val();
    var contentType = $("#contentType").val();
    var isHideClosedStatus = $('#isHideCloseStatus').is(':checked');
    var type = "";
    var subType = "";
    if (contentType == "case") {
        type = $('#caseType').val();
        subType = $('#caseSubType').val();
    } else if (contentType == "license") {
        type = $('#licenseType').val();
        subType = $('#licenseSubType').val();
    }

    $(".loading").show();
    if ($.fn.DataTable.isDataTable('#publicContentTable')) {
        $('#publicContentTable').DataTable().clear().destroy();
    }

    // Base column list
    var columns = [
        {
            data: 'title',
            title: '#Reference',
            render: function (data, type, row) {
                if (!data) return '';                
                if (row.IsAllowPublicView && row.SubmissionType == row.caseDisplayText) {
                    return `<a href="/OrchardCore.Case/PublicCaseProfileDetails/${row.ContentItemId}?token=${$('#hiddenToken').val()}">${data}</a>`;
                }
                if (row.IsAllowPublicView && row.SubmissionType == row.licenseDisplayText) {
                    return `<a href="/OrchardCore.License/PublicLicenseProfileDetails/${row.ContentItemId}?token=${$('#hiddenToken').val()}">${data}</a>`;
                }
                return data;
            }
        },
        { data: 'submissionType', title: 'Classification', render: d => d ?? '' },
        { data: 'type', title: 'Type', render: d => d ?? '' },
        { data: 'subtype', title: 'Sub-Type', render: d => d ?? '' }        
    ];

    const showNameByDefault = $("#hiddenIsShowNameByDefault").val() === "True";
    columns.push({
        data: 'name',
        title: 'Name',
        visible: showNameByDefault,
        render: d => d ?? ''
    });

    columns.push({
        data: 'address',
        title: 'Address',
        render: d => d ?? ''
    });

    if ($("#hiddenIsShowPhoneNumberByDefault").val() === "True") {
        columns.push({
            data: 'phoneNumber',
            title: 'Phone Number',
            render: d => d ?? ''
        });
    }

    columns.push(
        {
            data: 'created',
            title: 'Created Date',
            type: 'date',
            render: function (data) {
                if (!data) return '';
                var date = new Date(data);
                return `${date.getMonth() + 1}/${date.getDate()}/${date.getFullYear()}`;
            }
        },
        {
            data: 'edited',
            title: 'Last Activity',
            type: 'date',
            render: function (data) {
                if (!data) return '';
                var date = new Date(data);
                return `${date.getMonth() + 1}/${date.getDate()}/${date.getFullYear()}`;
            }
        },
        { data: 'status', title: 'Status', render: d => d ?? '' },
        {
            data: 'applicationLocation',
            title: 'Map',
            render: function (data) {
                if (!data) return '';
                var a = JSON.parse(data);
                if (!a.Latitude && !a.Longitude) return '';
                return `<a class="btn btn-info btn-sm" title="${a.Address}" onclick="locationShowOnMap(${a.Latitude},${a.Longitude});"><i class="fas fa-map-marker-alt"></i></a>`;
            }
        },
        {
            data: 'submissionType',
            title: 'View',
            render: function (data, type, row) {
                if (!data) return '';
                if (data === row.licenseDisplayText && row.showOnFrontEndLicenseViewButton) {
                    return `<a onclick="ViewPrint('${row.contentItemId}')" style="cursor:pointer;color:#512f87d0;">View ${data}</a>`;
                }
                if (data === row.caseDisplayText && row.showCaseDetailsReport) {
                    return `<a target="_blank" href="PublicReport/GetAllCaseDetailsData/${row.contentItemId}" style="cursor:pointer;color:#512f87d0;">View ${data}</a>`;
                }
                return `<label>No Public View Available</label>`;
            }
        }
    );

    // Conditionally add a column
    if ($("#hiddenIsInspectionScoreShowOnActivitySearchTool").val() == "True") {
        columns.splice(13, 0, {
            data: 'submissionType',
            title: 'Score',
            render: function (data, type, row) {
                if (!data) { return '' }
                var viewInspectionScore = '';
                if (data == row.caseDisplayText && $("#hiddenIsInspectionScoreShowOnActivitySearchTool").val() == "True") {
                    viewInspectionScore = `<a style="cursor: pointer;color:#512f87d0;" onclick="ViewInspectionScore('${row.contentItemId}','')">View Score</a>`;
                } else if (data == row.licenseDisplayText && $("#hiddenIsInspectionScoreShowOnActivitySearchTool").val() == "True") {
                    viewInspectionScore = `<a style="cursor: pointer;color:#512f87d0;" onclick="ViewInspectionScore('','${row.contentItemId}')">View Score</a>`;
                }

                return viewInspectionScore;
            }
        });
    }

    if (contentType === "license" || contentType === "All") {
        const statusIndex = columns.findIndex(col => col.title === 'Status');
        columns.splice(statusIndex + 1, 0, {
            data: 'businessName',
            title: 'Business Name',
            render: (data, type, row) =>
                row.submissionType === row.licenseDisplayText ? (data ?? '') : ''
        });
    }

    var nonOrderItemList = [];
    var nonOrderableFields = [
        "subtype",
        "name",
        "address",
        "phoneNumber",
        "status",
        "applicationLocation"
    ];
    columns.forEach((col, index) => {
        if (nonOrderableFields.includes(col.data)) {
            nonOrderItemList.push(index);
        }

        if (["Score", "Map", "View"].includes(col.title)) {
            nonOrderItemList.push(index);
        }
    });

    activitySearchTable = $('#publicContentTable').DataTable({
        processing: true,
        serverSide: true,
        searching: false,
        responsive: true,
        autoWidth: false,
        order: [[7, "desc"]],
        rowReorder: {
            selector: 'td:nth-child(2)'
        },
        columnDefs: [
            { orderable: false, targets: nonOrderItemList }
        ],
        pageLength: datatablePageSize ? parseInt(datatablePageSize) : 25,
        ajax: {
            url: urlConfig.GetAllContentToolModels,
            type: 'GET',
            data: function (d) {
                const columnMap = {
                    0: "Reference",
                    1: "Classification",
                    2: "Type",
                    3: "Sub-Type",
                    4: "Name",
                    5: "Address",
                    6: "Phone Number",
                    7: "Created Date",
                    8: "Last Activity",
                    9: "Status"
                };

                const pageNumber = (d.start / d.length) + 1;
                const pageSize = d.length || 10;

                let type = '';
                let subType = '';

                if (contentType === "case") {
                    type = $('#hiddenCaseTypeId').val();
                    subType = $('#hiddenCaseSubTypeId').val();
                } else if (contentType === "license") {
                    type = $('#hiddenLicenseTypeId').val();
                    subType = $('#hiddenLicenseSubTypeId').val();
                }

                return {
                    searchText: thisSubString,
                    filter: filterString,
                    contentType: contentType,
                    type: type,
                    days: $('#days-dropdown').val(),
                    subType: subType,
                    isHideClosedStatus: isHideClosedStatus,
                    Start: pageNumber,
                    Length: pageSize,
                    SortBy: columnMap[d.order?.[0]?.column] || "Created Date",
                    SortType: d.order?.[0]?.dir || "desc",
                    draw: d.draw // Keep for draw count sync
                };
            },
            dataSrc: function (json) {
                $(".loading").hide();
                UpdateTableBody(json.data);
                return json.data;
            }
        },
        columns: columns,
        infoCallback: function (settings, start, end, max, total, pre) {
            return `Showing ${start} to ${end} of ${total} entries`;
        }
    });
    $('#publicContentTable').on('draw.dt', function () {
        $('[data-bs-toggle="tooltip"]').tooltip();
    });

    $('#publicContentTable').on('length.dt', function (e, settings, len) {
        datatablePageSize = len;
    });

    activitySearchTable.on('preXhr.dt', function () {
        $(".loading").show();
    });

    activitySearchTable.on('xhr.dt', function () {
        $(".loading").hide();
    });
}
function UpdateTableBody(jsonArray) {
    var mapObj = [];
    jsonArray.forEach(e => {
        if (e.applicationLocation) {
            var addressObj = JSON.parse(e.applicationLocation);
        }

        if (e.applicationLocation !== null && e.applicationLocation !== "") {
            mapObj.push({
                title: e.title,
                status: e.status,
                address: addressObj,
                contentType: e.type,
                contentItemID: e.contentItemId,
                editLink: "",
                mapPin: e.mapPin,
                submissionType: e.submissionType,
            });
        }
    });
    if (Esri_Map.MapView) {
        Esri_Map.bindMap(mapObj);
    }
}

function ViewPrint(id) {
    $(".loading").show();
    $.ajax({
        url: urlConfig.GetLicenseFormat,
        async: true,
        method: 'GET',
        data: {
            contentItemId: id
        },
        success: function (e) {
            $(".loading").hide();
            if (Object.keys(e).length > 0) {
                var format = e.licenseFormat;
                $("#LicenceContainerFormat").empty();
                $("#LicenceContainerDoc").empty();
                if (format !== "") {
                    $("#LicenceContainerFormat").html(format);
                }
                var docName = e.licenseFormatDoc;
                if (docName !== "") {
                    $("#LicenceContainerDoc").html(`<a href="OrchardCore.License/DownloadLicenseWordDoc?url=${docName}&contentItemId=${id}" target="_blank"><i class="fa fa-download" aria-hidden="true"></i> Download License</a>`);
                }
                $("#LicenseFormatModal").modal("show");
            }
        },
        error: function (error) { $(".loading").hide(); console.log(error); }
    });

}
function printlicense() {
    setTimeout(function () {
        var licenceContainerFormatValue = $("#LicenceContainerFormat").html();
        var printWindow = window.open('', '_blank');
        printWindow.document.write('<html><head><title>Licence</title></head><body>');
        printWindow.document.write('<p>' + licenceContainerFormatValue + '</p>');
        printWindow.document.write('</body></html>');
        printWindow.document.close();
        printWindow.onload = function () {
            printWindow.print();
            printWindow.close();
        };
    }, 1000);
}

function ViewInspectionScore(caseId, licenseId) {
    $(".loading").show();
    $.ajax({
        url: urlConfig.GetCaseOrLicenseInspectionsByCaseIdOrLicenseId,
        async: true,
        method: 'GET',
        data: {
            caseId: caseId,
            licenseId: licenseId,
        },
        success: function (data) {
            $(".loading").hide();
            $("#inspectionScoreTable tbody").html('');
            document.getElementById('noDataMessage').style.display = 'none';
            const tableBody = document.querySelector('#inspectionScoreTable tbody');
            tableBody.innerHTML = ''; // Clear existing rows
            if (data != null && data.length > 0) {
                data.forEach((item, index) => {
                    var appointmentDate = '';
                    if (item.appointmentDate != null) {
                        appointmentDate = new Date(item.appointmentDate).toLocaleDateString();
                    }

                    const row = `
        <tr>
          <td>${item.type}</td>
          <td>${item.score}</td>
          <td>${appointmentDate}</td>
          <td>${item.body}</td>
        </tr>
      `;
                    tableBody.innerHTML += row;
                });
            } else {
                document.getElementById('noDataMessage').style.display = 'block';
            }

            $("#inspectionScoreModal").modal("show");
        },
        error: function (error) { $(".loading").hide(); console.log(error); }
    });
}

function initSearchTool(isExpandByDefault, searchBy, contentType, days) {
    $(".loading").show();
    $('#advancedSearch').toggleClass('hidden');
    $('#arrowClick').click(function () {
        $('#advancedSearch').toggleClass('hidden');
        $('.activity-item-btn').toggleClass('fa-caret-down fa-caret-up');
    });

    $(".item-list-view").click(function () {
        if (activitySearchTable) {
            activitySearchTable.columns.adjust();
        }
    });

    if (isExpandByDefault) {
        $('#arrowClick').toggleClass('hidden');
        $('.activity-item-btn').toggleClass('fa-caret-down fa-caret-up');
    }
    $('#advancedSearch').toggleClass('hidden');
    PrefillValues(searchBy, contentType, days);
    GetSearchByFilterValue();
}

$(document).on('change', '#filter-dropdown, #contentSearchBar, #days-dropdown, #contentType, #isHideCloseStatus', function (event) {
    SearchActivityToolData(event.target.id);
})

let dropdownChanged = false;
$(document).on('change', '.multiselect-container input', function () {
    dropdownChanged = true;
});


$(document).ready(function () {
    caseType_Picker.onDropdownClosed = function () {
        if (dropdownChanged) {
            SearchActivityToolData("caseType_Select");
        }
        dropdownChanged = false;
    }
    caseSubType_Picker.onDropdownClosed = function () {
        if (dropdownChanged) {
            SearchActivityToolData("caseSubType_Select");
        }
        dropdownChanged = false;
    }
    licenseType_Picker.onDropdownClosed = function () {
        if (dropdownChanged) {
            SearchActivityToolData("licenseType_Select");
        }
        dropdownChanged = false;
    }
    licenseSubType_Picker.onDropdownClosed = function () {
        if (dropdownChanged) {
            SearchActivityToolData("licenseSubType_Select");
        }
        dropdownChanged = false;
    }
})

function PrefillValues(searchBy, contentType, days) {
    $("#filter-dropdown").val(searchBy);
    $("#contentType").val(contentType);
    $("#days-dropdown").val(days);
    ManageTypeAndSubTypeDivs();
}

function SearchActivityToolData(changeEventId) {
    $(".loading").show();
    var searchBy = $("#filter-dropdown").val();
    if (changeEventId === "filter-dropdown" && searchBy === 'BusinessName'){
        $("#contentType").val('license');
    }
    var searchText = $("#contentSearchBar").val();
    var contentType = $("#contentType").val();
    var days = $("#days-dropdown").val();
    var typeDisplayText = "";
    var subTypeDisplayText = "";
    var isHideClosedItem = $("#isHideCloseStatus").prop('checked') ? "true" : "false";

    if (contentType.toLowerCase() === "all" && searchBy === 'BusinessName') {
      $('#filter-dropdown').val('ReferenceNumber');
      searchBy = $("#filter-dropdown").val();
    }

    if (contentType.toLowerCase() === "case") {
        if (searchBy === 'BusinessName') {
          $('#filter-dropdown').val('ReferenceNumber');
          searchBy = $("#filter-dropdown").val();
        }
        typeId = $("#caseType_Select").val();
        typeDisplayText = $('#caseType_Select option:selected').map(function () {
            return $(this).text();
        }).get().join(', ');

        if (changeEventId == "caseType_Select") {
            subTypeId = subTypeDisplayText = "";
        }
        else {
            subTypeId = $("#caseSubType_Select").val();
            subTypeDisplayText = $('#caseSubType_Select option:selected').map(function () {
                return $(this).text();
            }).get().join(', ');
        }
    }

    if (contentType.toLowerCase() === "license") {
        typeId = $("#licenseType_Select").val();
        typeDisplayText = $('#licenseType_Select option:selected').map(function () {
            return $(this).text();
        }).get().join(', ');

        if (changeEventId == "licenseType_Select") {
            subTypeId = subTypeDisplayText = "";
        }
        else {
            subTypeId = $("#licenseSubType_Select").val();
            subTypeDisplayText = $('#licenseSubType_Select option:selected').map(function () {
                return $(this).text();
            }).get().join(', ');
        }
    }

    var url = `/ActivitySearchTool?Filter=${encodeURIComponent(searchBy)}`
        + `&SearchText=${encodeURIComponent(searchText)}`
        + `&ContentType=${encodeURIComponent(contentType)}`
        + `&Type=${encodeURIComponent(typeDisplayText)}`
        + `&SubType=${encodeURIComponent(subTypeDisplayText)}`
        + `&IsHideClosedStatus=${encodeURIComponent(isHideClosedItem)}`
        + `&IsSearch=${encodeURIComponent("true")}`
        + `&Days=${encodeURIComponent(days)}`;

    const MAX_URL_LENGTH = 2000;
    if (url.length > MAX_URL_LENGTH) {
        $(".loading").hide();
        errorDialog({
            title: "Selection Limit Exceeded",
            message: "You have selected too many filters. Please remove some to proceed."
        });
    } else {
        window.location.href = url;
    }   
}

function ManageTypeAndSubTypeDivs() {
    var contentType = $("#contentType").val();

    // Hide both by default
    $('.case_filter, .license_filter').hide();

    if (contentType) {
        var type = contentType.toLowerCase();

        if (type === "case") {
            $('.case_filter').show();
        } else if (type === "license") {
            $('.license_filter').show();
        }
    }
}

