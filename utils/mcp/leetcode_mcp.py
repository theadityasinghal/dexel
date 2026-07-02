from mcp.server.fastmcp import FastMCP
import httpx

mcp = FastMCP("LeetCode MCP", host="0.0.0.0", port=8931)

LEETCODE_GRAPHQL = "https://leetcode.com/graphql"

QUERY = """
query userStats($username: String!) {
  matchedUser(username: $username) {
    username
    submitStats: submitStatsGlobal {
      acSubmissionNum {
        difficulty
        count
      }
    }
    profile {
      ranking
      reputation
    }
  }
}
"""

@mcp.tool()
async def get_user_stats(username: str) -> dict:
    """Get a LeetCode user's solved problem counts and ranking."""
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            LEETCODE_GRAPHQL,
            json={"query": QUERY, "variables": {"username": username}},
            headers={"Content-Type": "application/json"},
        )
        data = resp.json()

    user = data.get("data", {}).get("matchedUser")
    if not user:
        return {"error": f"User '{username}' not found"}

    stats = {s["difficulty"]: s["count"] for s in user["submitStats"]["acSubmissionNum"]}
    return {
        "username": user["username"],
        "ranking": user["profile"]["ranking"],
        "total_solved": stats.get("All", 0),
        "easy_solved": stats.get("Easy", 0),
        "medium_solved": stats.get("Medium", 0),
        "hard_solved": stats.get("Hard", 0),
    }

if __name__ == "__main__":
    mcp.run(transport="sse")