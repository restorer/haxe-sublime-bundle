package hxsublime;



import haxe.macro.Expr;

class Utils 
{

	

	@:macro public static function getTypeOfExpr (e:Expr):Expr {
		
		neko.Lib.println("Type:|||" + haxe.macro.TypeTools.toString(haxe.macro.Context.typeof(e)) + "|||");


		

		throw "myerror";

		return macro null;

	}


}