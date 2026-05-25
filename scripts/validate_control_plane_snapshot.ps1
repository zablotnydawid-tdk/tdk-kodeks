param(
    [string]$Root = "C:\KODEKS",
    [string]$SnapshotPath = "",
    [string]$SchemaPath = ""
)

$ErrorActionPreference = "Continue"

if (-not $SnapshotPath) {
    $SnapshotPath = Join-Path $Root "state\control_plane_status.json"
}
if (-not $SchemaPath) {
    $SchemaPath = Join-Path $Root "schemas\control_plane_status.schema.json"
}

$errors = New-Object System.Collections.Generic.List[string]

function Add-Error {
    param([string]$Message)
    $script:errors.Add($Message) | Out-Null
}

function Read-JsonFile {
    param(
        [string]$Path,
        [string]$Label
    )

    if (-not (Test-Path $Path)) {
        Add-Error "$Label missing: $Path"
        return $null
    }

    try {
        return Get-Content -Raw -Path $Path | ConvertFrom-Json
    }
    catch {
        Add-Error "$Label is not valid JSON: $($_.Exception.Message)"
        return $null
    }
}

function Test-DateTimeString {
    param(
        [string]$Value,
        [string]$Path
    )

    $parsed = [DateTimeOffset]::MinValue
    if (-not [DateTimeOffset]::TryParse($Value, [ref]$parsed)) {
        Add-Error "$Path must be a date-time string"
    }
}

function Get-ObjectPropertyNames {
    param([object]$Object)
    if ($null -eq $Object) {
        return @()
    }
    return @($Object.PSObject.Properties | ForEach-Object { $_.Name })
}

function Test-RequiredProperties {
    param(
        [object]$Object,
        [string[]]$Required,
        [string]$Path
    )

    $names = Get-ObjectPropertyNames $Object
    foreach ($propertyName in $Required) {
        if ($names -notcontains $propertyName) {
            Add-Error "$Path missing required property: $propertyName"
        }
    }
}

function Test-NoAdditionalProperties {
    param(
        [object]$Object,
        [string[]]$Allowed,
        [string]$Path
    )

    foreach ($propertyName in (Get-ObjectPropertyNames $Object)) {
        if ($Allowed -notcontains $propertyName) {
            Add-Error "$Path contains unexpected property: $propertyName"
        }
    }
}

function Test-EnumValue {
    param(
        [string]$Value,
        [string[]]$Allowed,
        [string]$Path
    )

    if ($Allowed -notcontains $Value) {
        Add-Error "$Path has invalid value '$Value'. Allowed: $($Allowed -join ', ')"
    }
}

$schema = Read-JsonFile -Path $SchemaPath -Label "schema"
$snapshot = Read-JsonFile -Path $SnapshotPath -Label "snapshot"

if ($null -eq $schema -or $null -eq $snapshot) {
    $errors | ForEach-Object { Write-Host $_ }
    exit 1
}

$rootRequired = @($schema.required)
$rootAllowed = @($schema.properties.PSObject.Properties | ForEach-Object { $_.Name })
$componentNames = @($schema.properties.components.required)
$componentRequired = @($schema.'$defs'.component_status.required)
$componentAllowed = @($schema.'$defs'.component_status.properties.PSObject.Properties | ForEach-Object { $_.Name })
$statusEnum = @($schema.'$defs'.component_status.properties.status.enum)
$driftEnum = @($schema.'$defs'.component_status.properties.drift_level.enum)

Test-RequiredProperties -Object $snapshot -Required $rootRequired -Path "snapshot"
Test-NoAdditionalProperties -Object $snapshot -Allowed $rootAllowed -Path "snapshot"

if ($snapshot.schema_version -ne "1.0.0") {
    Add-Error "snapshot.schema_version must be 1.0.0"
}
Test-DateTimeString -Value $snapshot.generated_at -Path "snapshot.generated_at"

if ($null -eq $snapshot.components) {
    Add-Error "snapshot.components missing"
}
else {
    Test-RequiredProperties -Object $snapshot.components -Required $componentNames -Path "snapshot.components"
    Test-NoAdditionalProperties -Object $snapshot.components -Allowed $componentNames -Path "snapshot.components"

    foreach ($componentName in $componentNames) {
        $component = $snapshot.components.$componentName
        if ($null -eq $component) {
            continue
        }

        $componentPath = "snapshot.components.$componentName"
        Test-RequiredProperties -Object $component -Required $componentRequired -Path $componentPath
        Test-NoAdditionalProperties -Object $component -Allowed $componentAllowed -Path $componentPath

        foreach ($field in @("name", "source")) {
            if ([string]::IsNullOrWhiteSpace($component.$field)) {
                Add-Error "$componentPath.$field must be a non-empty string"
            }
        }
        foreach ($field in @("notes", "next_action")) {
            if ($null -eq $component.$field) {
                Add-Error "$componentPath.$field must be present"
            }
        }

        Test-EnumValue -Value $component.status -Allowed $statusEnum -Path "$componentPath.status"
        Test-EnumValue -Value $component.drift_level -Allowed $driftEnum -Path "$componentPath.drift_level"
        Test-DateTimeString -Value $component.last_checked -Path "$componentPath.last_checked"
    }
}

if ($errors.Count -eq 0) {
    Write-Host "status-ok"
    exit 0
}

$errors | ForEach-Object { Write-Host $_ }
exit 1
