<#
.SYNOPSIS
	Finds program location by searching through registry uninstall entries.
#>

Param ($program_name)

Push-Location
Set-Location "hklm:"

$items = Get-ChildItem "hklm:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\"

Foreach ($item In $items)
{
	$DisplayName = Get-ItemProperty $item | Select DisplayName
	If ($DisplayName -Like "*$program_name*")
	{
		$location = Get-ItemProperty $item | Select InstallLocation
		$location.InstallLocation
		Break
	}
}

Pop-Location
