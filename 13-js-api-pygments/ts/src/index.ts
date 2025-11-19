import templateHtml from './template.html';

interface Env {
	PYTHON_RPC: Service;
}

// Type definition for the Python RPC service methods
interface HighlighterRpcService {
	highlight_code(code: string, language?: string): Promise<Map<string, string>>;
}

export default {
	async fetch(request, env, ctx): Promise<Response> {
		// Get the RPC stub from the Python worker
		const rpc = env.PYTHON_RPC as any as HighlighterRpcService;

		// Sample code to highlight
		const sampleCode = `
async function fetchUserData(userId: number): Promise<User> {
	const response = await fetch(\`/api/users/\${userId}\`);

	if (!response.ok) {
		throw new Error(\`HTTP error! status: \${response.status}\`);
	}

	const data = await response.json();
	return data as User;
}

// Usage example
const user = await fetchUserData(123);
console.log(\`Welcome, \${user.name}!\`);
`.trim();

		// Call the Pygments RPC method to highlight TypeScript code
		const result = await rpc.highlight_code(sampleCode, 'typescript');
		console.log('Highlight result: ', JSON.stringify(result));

		// Build the HTML page from template
		const html = templateHtml
			.replace('{{CSS}}', result.get('css') || '')
			.replace('{{LANGUAGE}}', result.get('language') || 'unknown')
			.replace('{{HIGHLIGHTED_CODE}}', result.get('html') || '');

		return new Response(html, {
			headers: { 'Content-Type': 'text/html' },
		});
	},
} satisfies ExportedHandler<Env>;
