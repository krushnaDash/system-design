import java.util.*;

/**
 * Warriors vs Boss Problem
 *
 * Pick two warriors i (front) and j (back).
 * - Front warrior i lasts H[i]/B seconds. During this time both i and j deal damage.
 * - Back warrior j then lasts H[j]/B seconds, dealing damage alone.
 *
 * Total damage = (D[i]*H[i] + D[j]*(H[i] + H[j])) / B
 *
 * Maximize: f(i,j) = D[i]*H[i] + D[j]*(H[i] + H[j])   (then divide by B)
 *
 * For fixed front warrior i, we want backup j that maximizes:
 *   D[j]*H[i] + D[j]*H[j]
 *
 * This is a linear function of x = H[i]:  y = D[j]*x + D[j]*H[j]
 *   slope = D[j],  intercept = D[j]*H[j]
 *
 * → Upper envelope problem → Li Chao Tree (O(N log N))
 *
 * Handling i == j exclusion:
 *   Li Chao tree stores one "winner" line per node. A query traverses O(log N) nodes.
 *   We collect ALL winner lines along the root-to-leaf path, evaluate each at x,
 *   and pick the best one whose index != i. This is correct and O(log N) per query.
 *
 * Complexity: O(N log N)
 * 
 * 
 * 
 */
public class WarriorsVsBoss {

    public static double getMaxDamageDealt(int N, int[] H, int[] D, int B) {
        int n = N;

        // Each warrior j defines a line: y = D[j]*x + D[j]*H[j]
        long[] slopes = new long[n];
        long[] intercepts = new long[n];
        for (int j = 0; j < n; j++) {
            slopes[j] = D[j];
            intercepts[j] = (long) D[j] * H[j];
        }

        // Coordinate compress query points (H[i] values)
        long[] xs = new long[n];
        for (int i = 0; i < n; i++) xs[i] = H[i];
        Arrays.sort(xs);
        xs = unique(xs);
        int M = xs.length;

        // Build Li Chao tree and insert all lines
        int treeSize = 4 * M;
        int[] tree = new int[treeSize];
        Arrays.fill(tree, -1);

        for (int j = 0; j < n; j++) {
            insertLine(tree, xs, 1, 0, M - 1, j, slopes, intercepts);
        }

        // For each warrior i as front, query at x = H[i]
        // Traverse Li Chao tree root-to-leaf, collect all winner lines,
        // pick the best one with index != i
        long globalBest = Long.MIN_VALUE;

        for (int i = 0; i < n; i++) {
            long x = H[i];
            long base = (long) D[i] * H[i];
            int xIdx = Arrays.binarySearch(xs, x);

            long[] result = queryExcluding(tree, xs, slopes, intercepts, 1, 0, M - 1, xIdx, x, i);

            long candidateScore = base + result[0];
            globalBest = Math.max(globalBest, candidateScore);
        }

        return (double) globalBest / B;
    }

    static long eval(long[] slopes, long[] intercepts, int lineIdx, long x) {
        return slopes[lineIdx] * x + intercepts[lineIdx];
    }

    static void insertLine(int[] tree, long[] xs, int node, int lo, int hi,
                           int newLine, long[] slopes, long[] intercepts) {
        if (lo == hi) {
            if (tree[node] == -1 ||
                eval(slopes, intercepts, newLine, xs[lo]) > eval(slopes, intercepts, tree[node], xs[lo])) {
                tree[node] = newLine;
            }
            return;
        }

        int mid = (lo + hi) / 2;
        int cur = tree[node];

        if (cur == -1) {
            tree[node] = newLine;
            return;
        }

        boolean leftBetter = eval(slopes, intercepts, newLine, xs[lo]) > eval(slopes, intercepts, cur, xs[lo]);
        boolean midBetter = eval(slopes, intercepts, newLine, xs[mid]) > eval(slopes, intercepts, cur, xs[mid]);

        if (midBetter) {
            tree[node] = newLine;
            newLine = cur;
        }

        if (lo == hi) return;

        if (leftBetter != midBetter) {
            insertLine(tree, xs, 2 * node, lo, mid, newLine, slopes, intercepts);
        } else {
            insertLine(tree, xs, 2 * node + 1, mid + 1, hi, newLine, slopes, intercepts);
        }
    }

    // Query Li Chao tree, returning best value from any line with index != excludeIdx
    static long[] queryExcluding(int[] tree, long[] xs, long[] slopes, long[] intercepts,
                            int node, int lo, int hi, int xIdx, long x, int excludeIdx) {
        // Returns [bestValueExcluding]
        long bestExcluding = Long.MIN_VALUE;

        // Check current node's line
        if (tree[node] != -1) {
            long v = eval(slopes, intercepts, tree[node], x);
            if (tree[node] != excludeIdx) {
                bestExcluding = Math.max(bestExcluding, v);
            }
        }

        if (lo == hi) {
            return new long[]{bestExcluding};
        }

        int mid = (lo + hi) / 2;
        long[] childResult;
        if (xIdx <= mid) {
            childResult = queryExcluding(tree, xs, slopes, intercepts, 2 * node, lo, mid, xIdx, x, excludeIdx);
        } else {
            childResult = queryExcluding(tree, xs, slopes, intercepts, 2 * node + 1, mid + 1, hi, xIdx, x, excludeIdx);
        }

        bestExcluding = Math.max(bestExcluding, childResult[0]);
        return new long[]{bestExcluding};
    }

    static long[] unique(long[] sorted) {
        if (sorted.length == 0) return sorted;
        int count = 1;
        for (int i = 1; i < sorted.length; i++) {
            if (sorted[i] != sorted[i - 1]) count++;
        }
        long[] result = new long[count];
        result[0] = sorted[0];
        int idx = 1;
        for (int i = 1; i < sorted.length; i++) {
            if (sorted[i] != sorted[i - 1]) result[idx++] = sorted[i];
        }
        return result;
    }

    // ==================== TEST ====================
    public static void main(String[] args) {
        // Test case 1
        double r1 = getMaxDamageDealt(3, new int[]{2, 1, 4}, new int[]{3, 1, 2}, 4);
        System.out.printf("Test 1: %.6f (expected 6.500000)%n", r1);

        // Test case 2
        double r2 = getMaxDamageDealt(4, new int[]{1, 1, 2, 100}, new int[]{1, 2, 1, 3}, 8);
        System.out.printf("Test 2: %.6f (expected 62.750000)%n", r2);

        // Test case 3
        double r3 = getMaxDamageDealt(4, new int[]{1, 1, 2, 3}, new int[]{1, 2, 1, 100}, 8);
        System.out.printf("Test 3: %.6f (expected 62.750000)%n", r3);
    }
}
