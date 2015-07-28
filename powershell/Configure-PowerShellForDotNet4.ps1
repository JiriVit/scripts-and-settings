<#
.SYNOPSIS
	Configures PowerShell to use CLR version 4.
#>

If ($PSVersionTable.CLRVersion.Major -Eq 4)
{
	Write-Host "PowerShell is configured correctly."
}
Else
{
	$path = (Get-Item -Path ".\PowerShell_Config\" -Verbose).FullName
	[Environment]::SetEnvironmentVariable("COMPLUS_ApplicationMigrationRuntimeActivationConfigPath", "$path", "User")
	Write-Host "Environment variable was set. Now please run this script once again to check if PowerShell is configured correctly."
}

Write-Host "`nPress any key to continue ..."
$x = $host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

