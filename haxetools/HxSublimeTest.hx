
package ;

using hxsublime.FindDeclaration;
import hxsublime.Utils;

using StringTools;

class HxSublimeTest {

	static function main () {
		hxsublime.FindDeclaration.__sublimeFindDecl("hey".substr, 1);
		hxsublime.FindDeclaration.__sublimeShowDoc(StringTools.htmlUnescape, 1);
		hxsublime.FindDeclaration.__sublimeShowDoc("hey".substr, 1);

		hxsublime.FindDeclaration.__sublimeShowDoc(Iterator, 2);

		hxsublime.FindDeclaration.__sublimeShowDoc("".endsWith, 1);
		hxsublime.FindDeclaration.__getType("".endsWith, 1);
		
	}

}