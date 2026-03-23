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

import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import {
  WdkMcpServer,
  WALLET_TOOLS,
  PRICING_TOOLS,
  LENDING_TOOLS,
  BRIDGE_TOOLS,
} from '@tetherto/wdk-mcp-toolkit';
import WDK from '@tetherto/wdk';
import WalletManagerEvm from '@tetherto/wdk-wallet-evm';
import WalletManagerSolana from '@tetherto/wdk-wallet-solana';
import AaveProtocolEvm from '@tetherto/wdk-protocol-lending-aave-evm';
import Usdt0ProtocolEvm from '@tetherto/wdk-protocol-bridge-usdt0-evm';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const SEED_FILE = path.join(__dirname, '.seed');

async function main() {
  // Seed resolution order: env var → .seed file → auto-generate + persist
  let seed = process.env.WDK_SEED;

  if (!seed || !WDK.isValidSeed(seed)) {
    // Try loading from persisted .seed file
    try {
      if (fs.existsSync(SEED_FILE)) {
        seed = fs.readFileSync(SEED_FILE, 'utf8').trim();
        if (WDK.isValidSeed(seed)) {
          console.error('Loaded wallet seed from .seed file');
        } else {
          seed = null;
        }
      }
    } catch (_) { seed = null; }

    // Auto-generate and persist if still no valid seed
    if (!seed || !WDK.isValidSeed(seed)) {
      seed = WDK.getRandomSeedPhrase();
      fs.writeFileSync(SEED_FILE, seed, 'utf8');
      console.error('Auto-generated new wallet seed and saved to .seed file');
      console.error('This seed will persist across restarts.');
    }
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

  // 2b. Register Solana
  server.registerWallet('solana', WalletManagerSolana, {
    rpcUrl: process.env.SOLANA_RPC || 'https://api.mainnet-beta.solana.com',
  });

  // 3. Register Aave V3 lending on Ethereum (idle treasury yield)
  server.registerProtocol('ethereum', 'aave', AaveProtocolEvm);

  // 3b. Register USDT0 cross-chain bridge (LayerZero) on Ethereum
  server.registerProtocol('ethereum', 'usdt0', Usdt0ProtocolEvm);

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
  server.registerToken('solana', 'USDT', {
    address: 'Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB',
    decimals: 6,
  });

  // 6. Register all tools (wallet + pricing + lending)
  server.registerTools([
    ...WALLET_TOOLS,
    ...PRICING_TOOLS,
    ...LENDING_TOOLS,
    ...BRIDGE_TOOLS,
  ]);

  // 7. Connect via stdio transport (Python agent connects as subprocess)
  const transport = new StdioServerTransport();
  await server.connect(transport);

  console.error('WDK MCP Server running on stdio');
  console.error('Registered chains:', server.getChains());
  console.error('Registered lending protocols:', server.getLendingChains());
  console.error('Seed persisted:', fs.existsSync(SEED_FILE) ? 'yes (.seed file)' : 'env only');
}

main().catch((error) => {
  console.error('Fatal error:', error);
  process.exit(1);
});
