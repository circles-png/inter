export function getStreamEndpoint(server: string, protocol: string, path: string, port: string = "5001"): string {
	return `${protocol}://${server}:${port}/api/v1/${path}`;
}
