package com.scenicdrive.routing;

import static org.junit.jupiter.api.Assertions.assertEquals;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.ValueSource;

/**
 * The whole contract of ScenicScoreParser.parse, run during `mvn package` in the image build (the Dockerfile
 * no longer passes -DskipTests for this module), so an image that carries a broken parser is never produced.
 *
 * The read-back test in services/routing/tests can only see the scores the canyon window actually contains
 * (0..8); everything else about the contract - the no-tag default, the out-of-range clamp, garbage, the
 * values above the window's maximum - lives here, on the shipping symbol the TagParser calls.
 */
final class ScenicScoreParserTest {

    @ParameterizedTest
    @ValueSource(ints = {0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10})
    void everyValueInTheContractsRangeSurvivesUnchanged(int value) {
        assertEquals(value, ScenicScoreParser.parse(Integer.toString(value)),
                "scenic_score=" + value + " is inside the contract's 0..10 and must round-trip exactly");
    }

    @Test
    void noTagIsNoEvidenceAndScoresZero() {
        assertEquals(0, ScenicScoreParser.parse(null), "a way with no scenic_score tag");
        assertEquals(0, ScenicScoreParser.parse(""), "handleWayTags passes \"\" when the tag is absent");
        assertEquals(0, ScenicScoreParser.parse("   "), "blank is no evidence, never an average");
    }

    @ParameterizedTest
    @ValueSource(strings = {"-1", "-8", "0"})
    void atOrBelowZeroIsZero(String raw) {
        assertEquals(0, ScenicScoreParser.parse(raw), raw + " is not a score");
    }

    @ParameterizedTest
    @ValueSource(strings = {"11", "15", "99", "2147483647"})
    void aboveTheCeilingClampsRatherThanLosingTheWay(String raw) {
        assertEquals(ScenicScoreParser.MAX, ScenicScoreParser.parse(raw),
                raw + " is above the contract's ceiling and must clamp to " + ScenicScoreParser.MAX);
    }

    @ParameterizedTest
    @ValueSource(strings = {"scenic", "7,0", "seven", "8.0", "7.0", "1e1", "0x7", "", "+"})
    void garbageIsNoEvidence(String raw) {
        assertEquals(0, ScenicScoreParser.parse(raw),
                "'" + raw + "' is not an integer: unparsable is the same as no evidence (T-0213 ruling - "
                        + "the ETL writes integers, so '7.0' is a writer defect, not a 7)");
    }

    @Test
    void surroundingWhitespaceIsTrimmedNotRejected() {
        assertEquals(7, ScenicScoreParser.parse(" 7 "),
                "osmium and hand edits leave padding; ' 7 ' is a 7, not garbage (T-0213 ruling)");
        assertEquals(7, ScenicScoreParser.parse("\t7\n"), "any surrounding whitespace");
    }

    @Test
    void theEncodedValueIsWideEnoughForTheContract() {
        assertEquals(10, ScenicScoreParser.MAX, "the contract's ceiling");
        assertEquals(4, ScenicScoreParser.BITS, "4 unsigned bits hold 0..15, so 0..10 fits");
        assertEquals("scenic_score", ScenicScoreParser.KEY, "the tag key the ETL writes");
    }
}
