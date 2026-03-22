// PayStream WDK MCP Server
// Exposes multi-chain wallet operations (transfer, balance, Aave lending)
// as MCP tools for the Python LangGraph agent to call via stdio transport

// CRITICAL: Intercept stdout BEFORE any imports.
// The WDK library internally logs RPC errors to stdout which breaks
// the MCP JSON-RPC protocol. We redirect any non-JSON-RPC stdout to stderr.
const _origStdoutWrite = process.stdout.write.bind(process.stdout);
process.stdout.write = function (chunk, encoding, callback) {
  const str = typeof chunk === 'string' ? chunk : chunk.toString();
  const trimmed = str.trim();
  // Only allow lines that look like valid JSON-RPC (start with '{')
  // Everything else goes to stderr so MCP protocol stays clean
  if (trimmed.startsWith('{') || trimmed === '') {
    return _origStdoutWrite(chunk, encoding, callback);
  }
  // Redirect non-JSON to stderr
  process.stderr.write(chunk, encoding, callback);
  return true;
};

import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import {
  WdkMcpServer,
  WALLET_TOOLS,
  PRICING_TOOLS,
  LENDING_TOOLS,
} from '@tetherto/wdk-mcp-toolkit';
import WDK from '@tetherto/wdk';
import WalletManagerEvm from '@tetherto/wdk-wallet-evm';
import AaveProtocolEvm from '@tetherto/wdk-protocol-lending-aave-evm';

async function main() {
  // Auto-generate seed if not provided or invalid (for dev/demo)
  let seed = process.env.WDK_SEED;
  if (!seed || !WDK.isValidSeed(seed)) {
    const reason = seed ? 'Invalid WDK_SEED provided' : 'No WDK_SEED provided';
    seed = WDK.getRandomSeedPhrase();
    console.error(`${reason} — auto-generated a new wallet seed.`);
    console.error('Save this seed to persist your wallet across restarts:');
    console.error(`  WDK_SEED="${seed}"`);
  }

  const server = new WdkMcpServer('paystream-wdk', '1.0.0');

  // 1. Initialize WDK with seed
  server.useWdk({ seed });

  // 2. Register EVM chains (multi-chain: Polygon + Ethereum + Arbitrum)
  server.registerWallet('polygon', WalletManagerEvm, {
    provider: process.env.POLYGON_RPC || 'https://polygon.llamarpc.com',
  });
  server.registerWallet('ethereum', WalletManagerEvm, {
    provider: process.env.ETH_RPC || 'https://eth.llamarpc.com',
  });
  server.registerWallet('arbitrum', WalletManagerEvm, {
    provider: process.env.ARB_RPC || 'https://arbitrum.llamarpc.com',
  });

  // 3. Register Aave V3 lending on Ethereum (idle treasury yield)
  server.registerProtocol('ethereum', 'aave', AaveProtocolEvm);

  // 4. Enable pricing (Bitfinex, no API key needed)
  server.usePricing();

  // 5. Register USDT tokens on each chain
  server.registerToken('polygon', 'USDT', {
    address: '0xc2132D05D31c914a87C6611C10748AEb04B58e8F',
    decimals: 6,
  });
  server.registerToken('ethereum', 'USDT', {
    address: '0xdAC17F958D2ee523a2206206994597C13D831ec7',
    decimals: 6,
  });
  server.registerToken('arbitrum', 'USDT', {
    address: '0xFd086bC7CD5C481DCC9C85ebE478A1C0b69FCbb9',
    decimals: 6,
  });

  // 6. Register all tools (wallet + pricing + lending)
  server.registerTools([
    ...WALLET_TOOLS,
    ...PRICING_TOOLS,
    ...LENDING_TOOLS,
  ]);

  // 7. Connect via stdio transport (Python agent connects as subprocess)
  const transport = new StdioServerTransport();
  await server.connect(transport);

  console.error('WDK MCP Server running on stdio');
  console.error('Registered chains:', server.getChains());
  console.error('Registered lending protocols:', server.getLendingChains());
}

main().catch((error) => {
  console.error('Fatal error:', error);
  process.exit(1);
});
