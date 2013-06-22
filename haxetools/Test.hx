
package ;

using hxsublime.FindDeclaration;
import hxsublime.Utils;

using StringTools;

class Test {

	static function main () {
		hxsublime.FindDeclaration.__sublimeFindDecl("hey".substr, 1);
		hxsublime.FindDeclaration.__sublimeShowDoc(StringTools.htmlUnescape, 1);
		hxsublime.FindDeclaration.__sublimeShowDoc("hey".substr, 1);

		hxsublime.FindDeclaration.__sublimeShowDoc(Iterator, 1);

		hxsublime.FindDeclaration.__sublimeShowDoc("".endsWith, 1);
		hxsublime.FindDeclaration.__getType("".endsWith, 1);
		
	}

}